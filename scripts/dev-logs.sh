#!/bin/bash

# iTerm2 4象限日志脚本 - 使用原生分割窗格功能

# 检查是否在iTerm2中运行（更宽松的检查）
if [[ "$TERM_PROGRAM" != "iTerm.app" ]] && [[ "$LC_TERMINAL" != "iTerm2" ]] && [[ ! -n "$ITERM_SESSION_ID" ]]; then
    echo "⚠️  iTerm2 detection:"
    echo "    TERM_PROGRAM: $TERM_PROGRAM"
    echo "    LC_TERMINAL: $LC_TERMINAL" 
    echo "    ITERM_SESSION_ID: $ITERM_SESSION_ID"
    echo ""
    read -p "Continue anyway? This script works best in iTerm2 (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please use iTerm2 for the best experience, or try: ./scripts/dev-logs.sh"
        exit 1
    fi
    echo "Proceeding with current terminal..."
fi

# 检查是否在正确的目录
if [[ ! -f "docker-compose.dev.yml" ]]; then
    echo "❌ Please run this script from the project root directory"
    echo "Current directory: $(pwd)"
    echo "Expected files: docker-compose.dev.yml"
    exit 1
fi

echo "🚀 Setting up 4-Quadrant Development Logs with iTerm2..."
echo ""

# 获取当前工作目录
CURRENT_DIR=$(pwd)

# 使用iTerm2的AppleScript API创建分割窗格
osascript <<EOF
tell application "iTerm"
    -- 获取当前窗口和会话
    set currentWindow to current window
    set currentSession to current session of currentWindow
    
    -- 设置当前会话为Frontend日志
    tell currentSession
        write text "cd '$CURRENT_DIR' && echo '🌐 FRONTEND LOGS (Port 3000)' && echo '════════════════════════════════════════════════════════════════════════════════' && docker-compose -f docker-compose.dev.yml logs -f frontend"
    end tell
    
    -- 垂直分割 - 创建右侧窗格 (Ray)
    tell currentSession
        set raySession to (split vertically with default profile)
    end tell
    
    -- 设置Ray会话
    tell raySession
        write text "cd '$CURRENT_DIR' && echo '⚡ RAY CLUSTER LOGS (Port 8265)' && echo '════════════════════════════════════════════════════════════════════════════════' && docker-compose -f docker-compose.dev.yml logs -f ray-head ray-worker-default ray-worker-gpu"
    end tell
    
    -- 选择左侧窗格并水平分割 (Backend)
    tell currentSession
        set backendSession to (split horizontally with default profile)
    end tell
    
    -- 设置Backend会话
    tell backendSession
        write text "cd '$CURRENT_DIR' && echo '🐍 BACKEND LOGS (Port 8000)' && echo '════════════════════════════════════════════════════════════════════════════════' && docker-compose -f docker-compose.dev.yml logs -f backend"
    end tell
    
    -- 选择右上角窗格并水平分割 (Temporal)
    tell raySession
        set temporalSession to (split horizontally with default profile)
    end tell
    
    -- 设置Temporal会话
    tell temporalSession
        write text "cd '$CURRENT_DIR' && echo '🔄 TEMPORAL LOGS (Port 8080)' && echo '════════════════════════════════════════════════════════════════════════════════' && docker-compose -f docker-compose.dev.yml logs -f temporal temporal-worker"
    end tell
    
end tell
EOF

echo "✅ 4-Quadrant Logs Setup Complete!"
echo ""
echo "📋 Layout:"
echo "┌─────────────┬─────────────┐"
echo "│ Frontend    │ Ray Cluster │"
echo "│ :3000       │ :8265       │"
echo "├─────────────┼─────────────┤"
echo "│ Backend     │ Temporal    │"
echo "│ :8000       │ :8080       │"
echo "└─────────────┴─────────────┘"
echo ""
echo "🎉 Benefits of iTerm2 Native Splits:"
echo "  ✅ Each pane is a separate shell session"
echo "  ✅ Ctrl+C works normally in each pane"
echo "  ✅ Perfect text selection - no cross-pane issues"
echo "  ✅ Independent scrollback for each pane"
echo "  ✅ Native copy/paste with Cmd+C"
echo ""
echo "📋 iTerm2 Controls:"
echo "  Cmd+D                Split vertically"
echo "  Cmd+Shift+D          Split horizontally"
echo "  Cmd+[                Previous pane"
echo "  Cmd+]                Next pane"
echo "  Cmd+Option+Arrow     Navigate panes"
echo "  Cmd+W                Close current pane"
echo "  Cmd+Enter            Toggle pane zoom"
echo ""
echo "💡 Text Selection:"
echo "  → Click and drag normally - stays within pane boundaries"
echo "  → Cmd+C to copy, Cmd+V to paste"
echo "  → Option+Click to position cursor"
echo "  → Triple-click to select entire line"
echo ""