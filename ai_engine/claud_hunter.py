"""
ODIN-Hunter | AI Engine
Groq (kimi-k2 primary / llama-3.3-70b fallback) for vulnerability analysis
Anthropic available as optional override
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

AI_PROVIDER       = os.getenv("AI_PROVIDER", "gemini")
AI_MODEL          = os.getenv("AI_MODEL", "gemini-1.5-pro")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "moonshotai/kimi-k2")
GROQ_KEY          = os.getenv("GROQ_API_KEY", "")
ANTHROPIC_KEY     = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_KEY        = os.getenv("GEMINI_KEY", "")

ANALYSIS_PROMPT = """You are an expert bug bounty hunter AI assistant integrated into ODIN-Hunter.

Analyze these vulnerability findings from an automated scan and:
1. Filter out false positives (confidence < 0.5)
2. Confirm true positives and explain WHY it is a real finding
3. Score severity using CVSS v3 logic
4. Suggest specific proof-of-concept steps
5. Estimate bounty range based on severity

Target: {target}
Program: {program_id}

Raw Findings:
{findings}

Respond ONLY with valid JSON array. No markdown. No preamble. No backticks.
[
  {{
    "title": "string",
    "type": "string",
    "severity": "critical|high|medium|low|informational",
    "cvss_score": 0.0,
    "confidence": 0.0,
    "is_false_positive": false,
    "why_real": "explanation",
    "description": "detailed description",
    "proof": {{}},
    "poc_steps": ["step1", "step2"],
    "estimated_bounty_min": 0,
    "estimated_bounty_max": 0,
    "remediation": "string",
    "target": "string"
  }}
]"""


class ClaudeHunter:
    def __init__(self):
        self.groq_client = None
        self.anthropic_client = None
        self.gemini_client = None
        self._init_clients()

    def _init_clients(self):
        if GEMINI_KEY:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=GEMINI_KEY)
                print(f"[ClaudeHunter] Gemini ready | target: {AI_MODEL}")
            except Exception as e:
                print(f"[ClaudeHunter] Gemini init failed: {e} - pip install google-genai")

        if GROQ_KEY:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=GROQ_KEY)
                print(f"[ClaudeHunter] Groq ready | primary: {AI_MODEL} | fallback: {AI_FALLBACK_MODEL}")
            except Exception as e:
                print(f"[ClaudeHunter] Groq init failed: {e}")

        if ANTHROPIC_KEY and AI_PROVIDER == "anthropic":
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
                print("[ClaudeHunter] Anthropic ready")
            except Exception as e:
                print(f"[ClaudeHunter] Anthropic init failed: {e}")

    async def _call_groq(self, prompt: str, model: str, max_tokens: int = 4096) -> str:
        response = self.groq_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.1
        )
        return response.choices[0].message.content

    async def _call_with_fallback(self, prompt: str, max_tokens: int = 4096) -> str:
        """gemini-1.5-pro first, kimi-k2 if it fails"""
        
        if AI_PROVIDER == "gemini" and self.gemini_client:
            try:
                response = self.gemini_client.models.generate_content(
                    model=AI_MODEL,
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                print(f"[ClaudeHunter] Gemini {AI_MODEL} failed: {e} — falling back")

        if AI_PROVIDER == "anthropic" and self.anthropic_client:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        if not self.groq_client:
            raise RuntimeError("No AI client available")

        try:
            return await self._call_groq(prompt, "moonshotai/kimi-k2", max_tokens)
        except Exception as e:
            print(f"[ClaudeHunter] Kimi-k2 failed: {e} — switching to llama")
            return await self._call_groq(prompt, "llama-3.3-70b-versatile", max_tokens)

    async def analyze_findings(self, findings: list, target: str, program_id: str) -> list:
        if not findings:
            return []
        if not self.groq_client and not self.anthropic_client:
            print("[ClaudeHunter] No AI client — returning raw findings")
            return findings

        try:
            prompt = ANALYSIS_PROMPT.format(
                target=target,
                program_id=program_id,
                findings=json.dumps(findings, indent=2)
            )
            content = await self._call_with_fallback(prompt)
            content = content.strip()
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            analyzed = json.loads(content)
            confirmed = [f for f in analyzed if not f.get("is_false_positive", False)]
            print(f"[ClaudeHunter] {len(findings)} raw -> {len(confirmed)} confirmed")
            return confirmed

        except json.JSONDecodeError as e:
            print(f"[ClaudeHunter] JSON parse error: {e} — returning raw")
            return findings
        except Exception as e:
            print(f"[ClaudeHunter] Error: {e}")
            return findings

    async def generate_poc(self, finding: dict) -> str:
        prompt = f"""Generate a detailed professional proof-of-concept for this bug bounty finding.

Finding: {json.dumps(finding, indent=2)}

Include: step-by-step reproduction, expected vs actual behavior, impact, request/response examples.
Be technical and precise."""
        try:
            return await self._call_with_fallback(prompt, max_tokens=2048)
        except Exception as e:
            return f"PoC generation failed: {e}"

    async def prioritize_targets(self, programs: list) -> list:
        if not programs:
            return programs
        prompt = f"""Rank these bug bounty programs by hunting ROI.
Consider: payout ranges, scope size, tech stack, competition, response time.

Programs: {json.dumps(programs[:20], indent=2)}

Return ONLY a JSON array, no markdown:
[{{"id": "...", "priority": 1, "reason": "..."}}]"""
        try:
            content = await self._call_with_fallback(prompt, max_tokens=1024)
            content = content.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            print(f"[ClaudeHunter] prioritize error: {e}")
            return programs