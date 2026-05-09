# ── Start odin-hunter ─────────────────────────────────────
echo -e "${CYAN}[STARTUP] Starting odin-hunter (port 8010)...${NC}"
cd "$HUNTER_DIR"
python main.py >> "$LOG_DIR/hunter.log" 2>&1 &
HUNTER_PID=$!
echo $HUNTER_PID > "$LOG_DIR/hunter.pid"
sleep 3
if kill -0 $HUNTER_PID 2>/dev/null; then
    echo -e "  ${GREEN}✓ odin-hunter running (PID $HUNTER_PID)${NC}"
else
    echo -e "  ${RED}✗ odin-hunter failed to start — check logs/hunter.log${NC}"
fi
