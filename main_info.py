#!/usr/bin/env python3
"""
ODIN-INFO: Information Processing and Communication Hub
Main entry point for document processing, web research, and communication.
"""

import asyncio
import logging
from typing import Dict, Any, List
import json

from email_mod.email_reader import EmailReader
from email_mod.email_writer import EmailWriter
from email_mod.email_filter import EmailFilter
from email_mod.email_monitor import EmailMonitor
from documents.doc_creator import DocumentCreator
from documents.doc_reader import DocumentReader
from documents.doc_modifier import DocumentModifier
from documents.doc_converter import DocumentConverter
from images.image_generator import ImageGenerator
from images.image_analyzer import ImageAnalyzer
from images.image_editor import ImageEditor
from images.image_sender import ImageSender
from web.web_researcher import WebResearcher
from web.news_monitor import NewsMonitor
from web.source_analyzer import SourceAnalyzer
from code_reader.repo_analyzer import RepoAnalyzer
from code_reader.architecture_mapper import ArchitectureMapper
from code_reader.explanation_engine import ExplanationEngine
from transmit.sms_sender import SMSSender
from transmit.notification_sender import NotificationSender
from transmit.file_transmitter import FileTransmitter

class OdinInfo:
    """Main ODIN-INFO orchestrator"""
    
    def __init__(self):
        self.setup_logging()
        self.load_modules()
        self.active_monitors = {}
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('odin_info.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_modules(self):
        """Initialize all information modules"""
        self.logger.info("Loading ODIN-INFO modules...")
        
        # Email modules
        self.email_reader = EmailReader()
        self.email_writer = EmailWriter()
        self.email_filter = EmailFilter()
        self.email_monitor = EmailMonitor()
        
        # Document modules
        self.doc_creator = DocumentCreator()
        self.doc_reader = DocumentReader()
        self.doc_modifier = DocumentModifier()
        self.doc_converter = DocumentConverter()
        
        # Image modules
        self.image_generator = ImageGenerator()
        self.image_analyzer = ImageAnalyzer()
        self.image_editor = ImageEditor()
        self.image_sender = ImageSender()
        
        # Web modules
        self.web_researcher = WebResearcher()
        self.news_monitor = NewsMonitor()
        self.source_analyzer = SourceAnalyzer()
        
        # Code reader modules
        self.repo_analyzer = RepoAnalyzer()
        self.architecture_mapper = ArchitectureMapper()
        self.explanation_engine = ExplanationEngine()
        
        # Transmission modules
        self.sms_sender = SMSSender()
        self.notification_sender = NotificationSender()
        self.file_transmitter = FileTransmitter()
        
        self.logger.info("All information modules loaded successfully")
        
    async def process_email(self, action: str, **kwargs) -> Dict[str, Any]:
        """Process email-related tasks"""
        self.logger.info(f"Processing email action: {action}")
        
        try:
            if action == "read":
                return await self.email_reader.read_emails(**kwargs)
            elif action == "write":
                return await self.email_writer.compose_email(**kwargs)
            elif action == "filter":
                return await self.email_filter.filter_emails(**kwargs)
            elif action == "monitor":
                return await self.email_monitor.start_monitoring(**kwargs)
            else:
                return {"error": f"Unknown email action: {action}"}
                
        except Exception as e:
            self.logger.error(f"Email processing failed: {e}")
            return {"error": str(e)}
            
    async def process_document(self, action: str, **kwargs) -> Dict[str, Any]:
        """Process document-related tasks"""
        self.logger.info(f"Processing document action: {action}")
        
        try:
            if action == "create":
                return await self.doc_creator.create_document(**kwargs)
            elif action == "read":
                return await self.doc_reader.read_document(**kwargs)
            elif action == "modify":
                return await self.doc_modifier.modify_document(**kwargs)
            elif action == "convert":
                return await self.doc_converter.convert_document(**kwargs)
            else:
                return {"error": f"Unknown document action: {action}"}
                
        except Exception as e:
            self.logger.error(f"Document processing failed: {e}")
            return {"error": str(e)}
            
    async def conduct_research(self, topic: str, depth: str = "comprehensive") -> Dict[str, Any]:
        """Conduct web research on a topic"""
        self.logger.info(f"Conducting research on: {topic}")
        
        try:
            # Research the topic
            research_data = await self.web_researcher.research(topic, depth)
            
            # Analyze source credibility
            credible_sources = await self.source_analyzer.analyze_sources(research_data["sources"])
            
            # Create summary document
            summary = await self.doc_creator.create_summary(research_data, credible_sources)
            
            return {
                "topic": topic,
                "research_data": research_data,
                "credible_sources": credible_sources,
                "summary": summary
            }
            
        except Exception as e:
            self.logger.error(f"Research failed: {e}")
            return {"error": str(e)}
            
    async def analyze_codebase(self, repo_path: str) -> Dict[str, Any]:
        """Analyze a code repository"""
        self.logger.info(f"Analyzing codebase: {repo_path}")
        
        try:
            # Analyze repository structure
            repo_analysis = await self.repo_analyzer.analyze(repo_path)
            
            # Map architecture
            architecture = await self.architecture_mapper.map_architecture(repo_analysis)
            
            # Generate explanations
            explanations = await self.explanation_engine.explain_components(architecture)
            
            return {
                "repository": repo_path,
                "analysis": repo_analysis,
                "architecture": architecture,
                "explanations": explanations
            }
            
        except Exception as e:
            self.logger.error(f"Code analysis failed: {e}")
            return {"error": str(e)}
            
    async def run(self):
        """Main run loop"""
        self.logger.info("ODIN-INFO started")
        
        # Example: Conduct research
        research_result = await self.conduct_research("quantum computing applications", "comprehensive")
        print(f"Research result: {research_result}")
        
        # Example: Analyze a codebase
        # code_analysis = await self.analyze_codebase("/path/to/repo")
        # print(f"Code analysis: {code_analysis}")
        
        self.logger.info("ODIN-INFO shutdown complete")

if __name__ == "__main__":
    info = OdinInfo()
    asyncio.run(info.run())
