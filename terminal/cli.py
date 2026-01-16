"""
URWA Brain v3.5 - Terminal CLI
Professional, errorless command-line interface with comprehensive API integration
"""

import sys
import time
import asyncio
import subprocess
import os
from pathlib import Path
from typing import Dict, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")

# Install dependencies if needed
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.markdown import Markdown
    import aiohttp
    import requests
except ImportError:
    print("Installing required packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich", "requests", "aiohttp", "-q"])
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.markdown import Markdown
    import aiohttp
    import requests

console = Console()

# Configuration
API_URL = "http://localhost:8000"
USE_OLLAMA = False

# ========== CORE FUNCTIONS ==========

def print_banner():
    """Display URWA Brain banner with professional styling"""
    banner_panel = Panel(
        r"""[bold gradient(cyan,blue)]
    ██╗   ██╗██████╗ ██╗    ██╗ █████╗     ██████╗ ██████╗  █████╗ ██╗███╗   ██╗
    ██║   ██║██╔══██╗██║    ██║██╔══██╗    ██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║
    ██║   ██║██████╔╝██║ █╗ ██║███████║    ██████╔╝██████╔╝███████║██║██╔██╗ ██║
    ██║   ██║██╔══██╗██║███╗██║██╔══██║    ██╔══██╗██╔══██╗██╔══██║██║██║╚██╗██║
    ╚██████╔╝██║  ██║╚███╔███╔╝██║  ██║    ██████╔╝██║  ██║██║  ██║██║██║ ╚████║
     ╚═════╝ ╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
[/bold gradient(cyan,blue)]
                    [bold yellow]⚡ Autonomous Web Research Agent ⚡[/bold yellow]
                        [bold red]Version 3.5[/bold red] | [dim]Powered by AI[/dim]""",
        border_style="bold cyan",
        padding=(1, 2),
        title="[bold white]🤖 URWA Brain[/bold white]",
        subtitle="[dim]Created by OM CHOKSI (SANS)"
    )
    console.print(banner_panel)
    console.print()

def check_api_server() -> bool:
    """Check if backend API is running"""
    try:
        resp = requests.get(f"{API_URL}/api/v1/system/health", timeout=3)
        return resp.status_code == 200
    except requests.exceptions.ConnectionError:
        return False
    except requests.exceptions.Timeout:
        return False
    except Exception:
        return False

def start_backend():
    """Start backend server in new window"""
    console.print("[yellow]Starting backend server...[/yellow]")
    backend_dir = Path(__file__).parent.parent / "backend"
    
    if sys.platform == "win32":
        venv_activate = Path(__file__).parent.parent / "venv" / "Scripts" / "activate.bat"
        cmd = f'start "URWA Backend" cmd /k "cd /d {backend_dir} && call {venv_activate} && python run.py"'
        subprocess.Popen(cmd, shell=True)
    else:
        cmd = f"cd {backend_dir} && ../venv/bin/python run.py"
        subprocess.Popen(cmd, shell=True, start_new_session=True)
    
    console.print("[dim]Waiting for server to initialize...[/dim]")
    for _ in range(15):
        time.sleep(1)
        if check_api_server():
            console.print("[green]✓ Backend Online![/green]")
            return True
    
    console.print("[red]✗ Failed to start backend![/red]")
    return False

def check_services():
    """Check backend and Ollama status with enhanced UI"""
    global USE_OLLAMA
    
    # Create status table
    status_table = Table(
        show_header=True,
        header_style="bold magenta",
        border_style="cyan",
        title="[bold cyan]🔍 System Health Check[/bold cyan]",
        title_style="bold cyan",
        box=None
    )
    status_table.add_column("Service", style="bold white", width=20)
    status_table.add_column("Status", width=25)
    status_table.add_column("Details", style="dim")
    
    # Check Backend
    backend_online = check_api_server()
    
    if not backend_online:
        status_table.add_row(
            "🔌 Backend API",
            "[red]● OFFLINE[/red]",
            f"Not responding at {API_URL}"
        )
        status_table.add_row(
            "🧠 Ollama LLM",
            "[dim]○ PENDING[/dim]",
            "Waiting for backend"
        )
        console.print(status_table)
        console.print()
        
        if Confirm.ask("[yellow]⚡ Start Backend Server?[/yellow]", default=True):
            if not start_backend():
                console.print(Panel(
                    "[yellow]⚠ Please start backend manually:[/yellow]\n\n"
                    "  [cyan]cd backend[/cyan]\n"
                    "  [cyan]python run.py[/cyan]\n\n"
                    f"Backend should run at: [bold]{API_URL}[/bold]",
                    border_style="yellow",
                    title="Manual Start Required"
                ))
                sys.exit(1)
        else:
            console.print("[dim]Exiting...[/dim]")
            sys.exit(0)
        return
    
    # Backend is online
    status_table.add_row(
        "🔌 Backend API",
        "[green]● ONLINE[/green]",
        f"Connected at {API_URL}"
    )
    
    # Check Ollama
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if resp.status_code == 200:
            USE_OLLAMA = True
            status_table.add_row(
                "🧠 Ollama LLM",
                "[green]● DETECTED[/green]",
                "Local AI available"
            )
        else:
            status_table.add_row(
                "🧠 Ollama LLM",
                "[yellow]○ NOT RUNNING[/yellow]",
                "Using Cloud LLM"
            )
    except:
        status_table.add_row(
            "🧠 Ollama LLM",
            "[yellow]○ NOT FOUND[/yellow]",
            "Using Cloud LLM (Gemini/Groq)"
        )
    
    console.print(status_table)
    console.print()

async def call_api(endpoint: str, method: str = "POST", params: Dict = None, json_data: Dict = None, timeout: int = 180) -> Dict:
    """Make API call with proper error handling"""
    url = f"{API_URL}{endpoint}"
    
    try:
        async with aiohttp.ClientSession() as session:
            kwargs = {"timeout": aiohttp.ClientTimeout(total=timeout)}
            
            if params:
                kwargs["params"] = params
            if json_data:
                kwargs["json"] = json_data
            
            if method == "POST":
                async with session.post(url, **kwargs) as resp:
                    if resp.status == 422:
                        text = await resp.text()
                        return {"status": "error", "message": f"Validation Error: {text}"}
                    return await resp.json()
            else:
                async with session.get(url, **kwargs) as resp:
                    return await resp.json()
                    
    except aiohttp.ClientConnectorError:
        return {"status": "error", "message": f"Cannot connect to backend at {API_URL}"}
    except asyncio.TimeoutError:
        return {"status": "error", "message": "Request timeout - operation took too long"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def show_main_menu() -> str:
    """Display professional main menu with enhanced UI"""
    
    # Create menu panel
    menu_content = Table.grid(padding=(0, 4))
    menu_content.add_column(style="bold cyan", justify="left")
    menu_content.add_column(style="white", justify="left")
    menu_content.add_column(style="bold cyan", justify="left")
    menu_content.add_column(style="white", justify="left")
    
    menu_content.add_row(
        "🤖 [01]", "[bold yellow]Master AI[/bold yellow]      ",
        "🔍 [05]", "[bold white]Site Analyzer[/bold white]"
    )
    menu_content.add_row(
        "💬 [02]", "[bold white]Chat Mode[/bold white]       ",
        "📊 [06]", "[bold white]System Status[/bold white]"
    )
    menu_content.add_row(
        "📚 [03]", "[bold white]Deep Research[/bold white]   ",
        "🚪 [00]", "[bold red]Exit[/bold red]"
    )
    menu_content.add_row(
        "🕷️ [04]", "[bold white]Scraper Tool[/bold white]    ",
        "", ""
    )
    
    menu_panel = Panel(
        menu_content,
        border_style="bold cyan",
        title="[bold yellow]⚡ Main Menu ⚡[/bold yellow]",
        subtitle="[dim]Select an option below[/dim]",
        padding=(1, 2)
    )
    
    console.print(menu_panel)
    console.print()
    
    choice = Prompt.ask(
        "[bold cyan]┃[/bold cyan] [bold white]Enter your choice[/bold white]",
        choices=["01", "1", "02", "2", "03", "3", "04", "4", "05", "5", "06", "6", "00", "0"],
        default="01"
    )
    
    # Normalize (01 -> 1)
    if choice.startswith("0") and len(choice) > 1:
        choice = choice[1]
    
    return choice

async def call_api(endpoint: str, method: str = "POST", params: Dict = None, json_data: Dict = None, timeout: int = 180) -> Dict:
    """Make API call with proper error handling"""
    url = f"{API_URL}{endpoint}"
    
    try:
        async with aiohttp.ClientSession() as session:
            kwargs = {"timeout": aiohttp.ClientTimeout(total=timeout)}
            
            if params:
                kwargs["params"] = params
            if json_data:
                kwargs["json"] = json_data
            
            if method == "POST":
                async with session.post(url, **kwargs) as resp:
                    if resp.status == 422:
                        text = await resp.text()
                        return {"status": "error", "message": f"Validation Error: {text}"}
                    return await resp.json()
            else:
                async with session.get(url, **kwargs) as resp:
                    return await resp.json()
                    
    except aiohttp.ClientConnectorError:
        return {"status": "error", "message": f"Cannot connect to backend at {API_URL}"}
    except asyncio.TimeoutError:
        return {"status": "error", "message": "Request timeout - operation took too long"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ========== MODE HANDLERS ==========

async def master_ai_handler(query: str):
    """Handle ANY request with intelligent routing - The MASTER mode"""
    
    # Display query panel with Master AI branding
    console.print(Panel(
        f"[bold yellow]{query}[/bold yellow]",
        title="[bold yellow]🤖 Master AI Request[/bold yellow]",
        border_style="yellow",
        padding=(0, 2)
    ))
    console.print()
    
    # Show processing with dynamic spinner
    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[bold yellow]{task.description}[/bold yellow]"),
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("🧠 Analyzing request...", total=None)
        
        # Call the unified agent endpoint
        result = await call_api(
            "/api/v1/agent",
            method="POST",
            json_data={"input": query, "use_ollama": USE_OLLAMA},
            timeout=300  # 5 minutes for complex operations
        )
        
        progress.update(task, description="✅ Processing complete!")
    
    console.print()
    
    # Handle errors
    if result.get("status") == "error":
        console.print(Panel(
            f"[bold red]❌ Error[/bold red]\n\n{result.get('message')}",
            border_style="red",
            title="Error Details"
        ))
        return
    
    # Display results based on intent/type
    intent = result.get("intent", "unknown")
    result_data = result.get("result", {})
    result_type = result_data.get("type", "unknown")
    
    # Show what action was taken
    action_taken = result.get("action_taken", "Processed your request")
    console.print(Panel(
        f"[bold green]✓ {action_taken}[/bold green]\n[dim]Intent: {intent} | Confidence: {result.get('confidence', 0):.0%}[/dim]",
        border_style="green",
        title="[bold green]Action Summary[/bold green]"
    ))
    console.print()
    
    # Display results based on type
    if result_type == "research_analysis":
        # Research result
        if result_data.get("answer"):
            console.print(Panel(
                Markdown(result_data["answer"]),
                title="[bold cyan]📚 Research Results[/bold cyan]",
                border_style="cyan",
                padding=(1, 2)
            ))
            
            # Show sources
            if result_data.get("sources"):
                sources_table = Table(
                    show_header=True,
                    header_style="bold magenta",
                    border_style="dim cyan",
                    title="[bold magenta]📖 Sources[/bold magenta]",
                    box=None
                )
                sources_table.add_column("#", style="dim", width=4)
                sources_table.add_column("Source", style="white")
                sources_table.add_column("URL", style="blue underline", overflow="fold")
                
                for i, src in enumerate(result_data["sources"][:10], 1):
                    sources_table.add_row(
                        f"[{i}]",
                        src.get('title', 'Untitled')[:60],
                        src.get('url', 'N/A')[:80]
                    )
                
                console.print()
                console.print(sources_table)
    
    elif result_type == "scrape_result":
        # Single URL scrape result
        if result_data.get("success"):
            # Show extracted/analyzed data
            if result_data.get("extracted_data"):
                console.print(Panel(
                    Markdown(result_data["extracted_data"]),
                    title="[bold green]✨ Extracted Insights[/bold green]",
                    border_style="green",
                    padding=(1, 2)
                ))
            
            # Show stats
            stats_grid = Table.grid(padding=(0, 2))
            stats_grid.add_column(style="bold green")
            stats_grid.add_column(style="white")
            stats_grid.add_row("✅ Status:", "Success")
            stats_grid.add_row("🔗 URL:", result_data.get("url", "N/A")[:70])
            stats_grid.add_row("📏 Length:", f"{result_data.get('content_length', 0):,} characters")
            
            console.print()
            console.print(Panel(stats_grid, title="[bold cyan]📊 Scraping Stats[/bold cyan]", border_style="cyan"))
        else:
            console.print(Panel(
                f"[bold yellow]⚠️ Scraping Failed[/bold yellow]\n\n{result_data.get('error', 'Unknown error')}",
                border_style="yellow"
            ))
    
    elif result_type == "comparison_result":
        # Comparison of multiple URLs
        console.print(Panel(
            Markdown(result_data.get("comparison_analysis", "No analysis available")),
            title="[bold yellow]⚖️ Comparison Analysis[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        ))
        
        # Show stats
        console.print()
        stats_grid = Table.grid(padding=(0, 2))
        stats_grid.add_column(style="bold cyan")
        stats_grid.add_column(style="white")
        stats_grid.add_row("📊 URLs Scraped:", str(result_data.get("scraped_count", 0)))
        stats_grid.add_row("❌ Failed:", str(result_data.get("failed_count", 0)))
        stats_grid.add_row("🔗 URLs:", "\n".join(result_data.get("urls", [])[:5]))
        
        console.print(Panel(stats_grid, title="[bold cyan]Summary[/bold cyan]", border_style="cyan"))
    
    elif result_type == "multi_scrape_result":
        # Multiple URLs scraped
        console.print(Panel(
            Markdown(result_data.get("combined_analysis", "No analysis available")),
            title="[bold green]📊 Combined Analysis[/bold green]",
            border_style="green",
            padding=(1, 2)
        ))
        
        # Show individual results
        if result_data.get("individual_results"):
            console.print()
            results_table = Table(
                show_header=True,
                header_style="bold cyan",
                border_style="dim cyan",
                title="[bold cyan]📄 Individual Results[/bold cyan]",
                box=None
            )
            results_table.add_column("#", style="dim", width=4)
            results_table.add_column("URL", style="blue underline")
            results_table.add_column("Length", style="green", justify="right")
            
            for i, res in enumerate(result_data["individual_results"], 1):
                results_table.add_row(
                    f"[{i}]",
                    res.get("url", "")[:70],
                    f"{res.get('content_length', 0):,} chars"
                )
            
            console.print(results_table)
    
    elif result_type == "fact_check":
        # Fact check result
        verdict = result_data.get("verdict", "unverified")
        verdict_colors = {
            "likely_true": "green",
            "likely_false": "red",
            "partially_true": "yellow",
            "unverified": "white"
        }
        verdict_icons = {
            "likely_true": "✅",
            "likely_false": "❌",
            "partially_true": "⚠️",
            "unverified": "❓"
        }
        
        color = verdict_colors.get(verdict, "white")
        icon = verdict_icons.get(verdict, "❓")
        
        console.print(Panel(
            f"[bold {color}]{icon} {verdict.upper().replace('_', ' ')}[/bold {color}]\n\n"
            f"[bold white]Claim:[/bold white] {result_data.get('claim', '')}\n\n"
            f"{result_data.get('analysis', '')}",
            border_style=color,
            title=f"[bold {color}]🔍 Fact Check Result[/bold {color}]",
            padding=(1, 2)
        ))
        
        # Show sources
        if result_data.get("sources"):
            sources_table = Table(
                show_header=True,
                header_style="bold magenta",
                border_style="dim",
                title="[bold]📖 Verification Sources[/bold]",
                box=None
            )
            sources_table.add_column("#", style="dim", width=4)
            sources_table.add_column("Source", style="white")
            
            for i, src in enumerate(result_data["sources"][:10], 1):
                sources_table.add_row(f"[{i}]", src.get('title', 'Untitled')[:80])
            
            console.print()
            console.print(sources_table)
    
    elif result_type == "site_profile":
        # Site profiling result
        risk = result_data.get("risk_level", "unknown")
        risk_colors = {"low": "green", "medium": "yellow", "high": "red", "extreme": "bold red", "unknown": "white"}
        color = risk_colors.get(risk, "white")
        
        profile_table = Table(show_header=False, box=None, border_style="dim")
        profile_table.add_column("Property", style="bold cyan", width=25)
        profile_table.add_column("Value", style="white")
        
        profile_table.add_row("🔗 URL", result_data.get("url", ""))
        profile_table.add_row("⚠️ Risk Level", f"[{color}]{risk.upper()}[/{color}]")
        profile_table.add_row("🛡️ Protection", result_data.get("protection", "None"))
        profile_table.add_row("🎯 Strategy", result_data.get("recommended_strategy", "stealth"))
        profile_table.add_row("✅ Can Scrape", "Yes" if result_data.get("can_scrape") else "Difficult")
        
        console.print(Panel(
            profile_table,
            title="[bold yellow]🔍 Site Profile[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        ))
    
    else:
        # Generic result display
        console.print(Panel(
            Markdown(str(result_data)),
            title="[bold cyan]📄 Result[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        ))
    
    # Show follow-up suggestions
    if result.get("follow_up_suggestions"):
        console.print()
        follow_up_panel = "\n".join([f"• {s}" for s in result["follow_up_suggestions"][:3]])
        console.print(Panel(
            follow_up_panel,
            title="[bold magenta]💡 Follow-up Suggestions[/bold magenta]",
            border_style="magenta",
            padding=(0, 2)
        ))
    
    # Show processing time
    if result.get("processing_time"):
        console.print()
        console.print(f"[dim]⏱️  Completed in {result['processing_time']}s[/dim]")

async def chat_mode_handler(query: str):
    """Handle chat/research queries with enhanced UI"""
    
    # Display query panel
    console.print(Panel(
        f"[bold white]{query}[/bold white]",
        title="[bold cyan]💬 Your Question[/bold cyan]",
        border_style="cyan",
        padding=(0, 2)
    ))
    console.print()
    
    with Progress(
        SpinnerColumn(spinner_name="dots12"),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        BarColumn(complete_style="cyan", finished_style="green"),
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("🤖 AI is thinking...", total=None)
        
        result = await call_api(
            "/api/v1/research",
            method="POST",
            json_data={
                "query": query,
                "deep": False,
                "use_ollama": USE_OLLAMA
            }
        )
        
        progress.update(task, description="✅ Complete!")
    
    console.print()
    
    if result.get("status") == "error":
        console.print(Panel(
            f"[bold red]❌ Error[/bold red]\n\n{result.get('message')}",
            border_style="red",
            title="Error Details"
        ))
        return
    
    # Display answer with enhanced formatting
    if result.get("answer"):
        console.print(Panel(
            Markdown(result["answer"]),
            title="[bold green]✨ AI Response[/bold green]",
            border_style="green",
            padding=(1, 2)
        ))
        
        # Display sources in a table
        if result.get("sources"):
            sources_table = Table(
                show_header=True,
                header_style="bold cyan",
                border_style="dim",
                title="[bold cyan]📚 Sources[/bold cyan]",
                box=None
            )
            sources_table.add_column("#", style="dim", width=3)
            sources_table.add_column("Title", style="bold")
            sources_table.add_column("URL", style="blue underline")
            
            for i, src in enumerate(result["sources"][:5], 1):
                url = src.get("url", "")
                title = src.get("title", url[:50] + "..." if len(url) > 50 else url)
                sources_table.add_row(str(i), title, url)
            
            console.print()
            console.print(sources_table)
    else:
        console.print(Panel(str(result), title="Result", border_style="cyan"))

async def deep_research_handler(query: str):
    """Handle deep research queries with enhanced UI"""
    
    # Display research topic panel
    console.print(Panel(
        f"[bold white]{query}[/bold white]",
        title="[bold magenta]📚 Deep Research Topic[/bold magenta]",
        border_style="magenta",
        padding=(0, 2)
    ))
    
    console.print(Panel(
        "[yellow]⏱️ This may take 1-2 minutes[/yellow]\n"
        "[dim]Searching multiple sources, analyzing content, synthesizing information...[/dim]",
        border_style="yellow",
        title="[bold yellow]ℹ️ Info[/bold yellow]"
    ))
    console.print()
    
    with Progress(
        SpinnerColumn(spinner_name="point"),
        TextColumn("[bold magenta]{task.description}[/bold magenta]"),
        BarColumn(complete_style="magenta", finished_style="green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("🔬 Conducting deep research...", total=100)
        
        result = await call_api(
            "/api/v1/research",
            method="POST",
            json_data={
                "query": query,
                "deep": True,
                "use_ollama": USE_OLLAMA
            },
            timeout=300
        )
        
        progress.update(task, completed=100, description="✅ Research Complete!")
    
    console.print()
    
    if result.get("status") == "error":
        console.print(Panel(
            f"[bold red]❌ Error[/bold red]\n\n{result.get('message')}",
            border_style="red",
            title="Error Details"
        ))
        return
    
    # Display comprehensive answer with enhanced formatting
    if result.get("answer"):
        console.print(Panel(
            Markdown(result["answer"]),
            title="[bold green]✨ Research Results[/bold green]",
            border_style="green",
            padding=(1, 2)
        ))
        
        # Display sources in an enhanced table
        if result.get("sources"):
            sources_table = Table(
                show_header=True,
                header_style="bold magenta",
                border_style="dim cyan",
                title="[bold magenta]📖 Sources Analyzed[/bold magenta]",
                title_style="bold magenta",
                box=None
            )
            sources_table.add_column("#", style="dim cyan", width=4)
            sources_table.add_column("Source", style="bold white")
            sources_table.add_column("URL", style="blue underline", overflow="fold")
            
            for i, src in enumerate(result["sources"], 1):
                title = src.get('title', 'Untitled Source')
                url = src.get('url', 'N/A')
                sources_table.add_row(f"[{i}]", title, url)
            
            console.print()
            console.print(sources_table)
    else:
        console.print(Panel(str(result), title="Result", border_style="cyan"))

async def scraper_handler(url: str):
    """Handle URL scraping with enhanced UI"""
    
    # Display URL panel
    console.print(Panel(
        f"[bold white]{url}[/bold white]",
        title="[bold cyan]🕷️ Target URL[/bold cyan]",
        border_style="cyan",
        padding=(0, 2)
    ))
    console.print()
    
    # First, profile the site with enhanced display
    with Progress(
        SpinnerColumn(spinner_name="arc"),
        TextColumn("[bold yellow]{task.description}[/bold yellow]"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("🔍 Analyzing site protection...", total=None)
        profile = await call_api("/api/v1/strategy/profile-site", method="GET", params={"url": url})
        progress.update(task, description="✅ Analysis complete!")
    
    console.print()
    
    if profile.get("status") == "success" and profile.get("profile"):
        prof = profile["profile"]
        risk = prof.get("risk_level", "unknown")
        risk_colors = {"low": "green", "medium": "yellow", "high": "red", "extreme": "bold red"}
        risk_icons = {"low": "✅", "medium": "⚠️", "high": "🔴", "extreme": "💀"}
        color = risk_colors.get(risk, "white")
        icon = risk_icons.get(risk, "❓")
        
        # Create protection info table
        info_table = Table(show_header=False, box=None, border_style="dim")
        info_table.add_column("Property", style="bold cyan", width=20)
        info_table.add_column("Value", style="white")
        
        info_table.add_row("Risk Level", f"[{color}]{icon} {risk.upper()}[/{color}]")
        info_table.add_row("Strategy", f"[cyan]{prof.get('recommended_strategy', 'stealth')}[/cyan]")
        info_table.add_row("Protection", f"[yellow]{prof.get('protection', 'None detected')}[/yellow]")
        
        console.print(Panel(
            info_table,
            title="[bold yellow]🛡️ Protection Analysis[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        ))
        console.print()
    
    # Scrape with protected-scrape endpoint
    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        BarColumn(complete_style="cyan", finished_style="green"),
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("🕷️ Scraping with stealth mode...", total=None)
        
        result = await call_api(
            "/api/v1/protected-scrape",
            method="POST",
            params={"url": url, "instruction": "Extract main content"}
        )
        
        progress.update(task, description="✅ Scraping complete!")
    
    console.print()
    
    if result.get("status") == "success":
        # Extract content
        content = None
        if result.get("result", {}).get("data"):
            content = str(result["result"]["data"])
        elif result.get("content"):
            content = result["content"]
        
        if content:
            content_length = result.get('content_length', len(content))
            
            # Success panel with stats
            stats_grid = Table.grid(padding=(0, 2))
            stats_grid.add_column(style="bold green")
            stats_grid.add_column(style="white")
            stats_grid.add_row("✅ Status:", "Success")
            stats_grid.add_row("📏 Length:", f"{content_length:,} characters")
            stats_grid.add_row("🎯 Method:", "Stealth Scraping")
            
            console.print(Panel(
                stats_grid,
                title="[bold green]✨ Scraping Results[/bold green]",
                border_style="green"
            ))
            console.print()
            
            # Display content (escape markup to prevent conflicts)
            display_content = content[:2000] if len(content) > 2000 else content
            
            # Add truncation notice if needed
            if len(content) > 2000:
                console.print(Panel(
                    display_content,
                    title="[bold cyan]📄 Extracted Content (First 2000 chars)[/bold cyan]",
                    border_style="cyan",
                    padding=(1, 2),
                    markup=False  # Disable markup parsing
                ))
                console.print("[dim italic]... (content truncated for display, full content extracted)[/dim italic]")
            else:
                console.print(Panel(
                    display_content,
                    title="[bold cyan]📄 Extracted Content[/bold cyan]",
                    border_style="cyan",
                    padding=(1, 2),
                    markup=False  # Disable markup parsing
                ))
    else:
        console.print(Panel(
            f"[bold yellow]⚠️ Scraping Failed[/bold yellow]\n\n{result.get('message', 'Unknown error')}",
            border_style="yellow",
            title="Warning"
        ))

async def site_analyzer_handler(url: str):
    """Analyze site protection and structure with enhanced UI"""
    
    # Display URL panel
    console.print(Panel(
        f"[bold white]{url}[/bold white]",
        title="[bold magenta]🔍 Analyzing Site[/bold magenta]",
        border_style="magenta",
        padding=(0, 2)
    ))
    console.print()
    
    with Progress(
        SpinnerColumn(spinner_name="bouncingBar"),
        TextColumn("[bold magenta]{task.description}[/bold magenta]"),
        BarColumn(complete_style="magenta"),
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("🔬 Profiling site security...", total=None)
        
        result = await call_api("/api/v1/strategy/profile-site", method="GET", params={"url": url})
        
        progress.update(task, description="✅ Analysis complete!")
    
    console.print()
    
    if result.get("status") == "success" and result.get("profile"):
        prof = result["profile"]
        
        risk = prof.get("risk_level", "unknown")
        risk_colors = {"low": "green", "medium": "yellow", "high": "red", "extreme": "bold red"}
        risk_icons = {"low": "✅", "medium": "⚠️", "high": "🔴", "extreme": "💀"}
        color = risk_colors.get(risk, "white")
        icon = risk_icons.get(risk, "❓")
        
        # Create comprehensive analysis table
        analysis_table = Table(
            show_header=True,
            header_style="bold magenta",
            border_style="cyan",
            title=f"[bold magenta]🛡️ Site Protection Profile[/bold magenta]",
            box=None
        )
        analysis_table.add_column("Property", style="bold cyan", width=25)
        analysis_table.add_column("Value", style="white", width=40)
        analysis_table.add_column("Status", style="bold", width=15)
        
        # Risk level with icon
        analysis_table.add_row(
            "🎯 Risk Level",
            f"[{color}]{risk.upper()}[/{color}]",
            f"[{color}]{icon}[/{color}]"
        )
        
        # Protection type
        protection = prof.get("protection", "None detected")
        protection_color = "red" if protection.lower() != "none" else "green"
        analysis_table.add_row(
            "🛡️ Protection",
            f"[{protection_color}]{protection}[/{protection_color}]",
            "🔒" if protection.lower() != "none" else "🔓"
        )
        
        # JavaScript requirement
        needs_js = prof.get("needs_rendering", False)
        analysis_table.add_row(
            "⚙️ JavaScript Required",
            f"[yellow]Yes[/yellow]" if needs_js else "[green]No[/green]",
            "⚡" if needs_js else "✅"
        )
        
        # Recommended strategy
        strategy = prof.get("recommended_strategy", "stealth")
        strategy_colors = {"lightweight": "green", "stealth": "yellow", "ultra_stealth": "red"}
        strategy_color = strategy_colors.get(strategy, "cyan")
        analysis_table.add_row(
            "🎯 Recommended Strategy",
            f"[{strategy_color}]{strategy.replace('_', ' ').title()}[/{strategy_color}]",
            "🚀"
        )
        
        # Scraping feasibility
        can_scrape = risk in ["low", "medium"]
        analysis_table.add_row(
            "✅ Scraping Feasibility",
            "[green]Possible[/green]" if can_scrape else "[yellow]Difficult[/yellow]",
            "✅" if can_scrape else "⚠️"
        )
        
        console.print(Panel(
            analysis_table,
            border_style="magenta",
            padding=(1, 2)
        ))
        
        # Add recommendation panel
        if risk == "low":
            rec_text = "[green]✅ This site is easy to scrape. Standard methods will work.[/green]"
            rec_style = "green"
        elif risk == "medium":
            rec_text = "[yellow]⚠️ Moderate protection. Use stealth mode for best results.[/yellow]"
            rec_style = "yellow"
        elif risk == "high":
            rec_text = "[red]🔴 Strong protection. Ultra-stealth mode required.[/red]"
            rec_style = "red"
        else:
            rec_text = "[bold red]💀 Extreme protection. Scraping may be very difficult.[/bold red]"
            rec_style = "red"
        
        console.print()
        console.print(Panel(
            rec_text,
            title="[bold white]💡 Recommendation[/bold white]",
            border_style=rec_style,
            padding=(0, 2)
        ))
    else:
        console.print(Panel(
            f"[bold yellow]⚠️ Analysis Failed[/bold yellow]\n\n{result.get('message', 'Unknown error')}",
            border_style="yellow",
            title="Warning"
        ))

async def system_status_handler():
    """Display system health and metrics with enhanced UI"""
    
    with Progress(
        SpinnerColumn(spinner_name="simpleDotsScrolling"),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("📊 Fetching system metrics...", total=None)
        health = await call_api("/api/v1/system/health", method="GET")
        progress.update(task, description="✅ Metrics retrieved!")
    
    console.print()
    
    if health.get("status") == "error":
        console.print(Panel(
            f"[bold red]❌ Error[/bold red]\n\n{health.get('message')}",
            border_style="red",
            title="Error"
        ))
        return
    
    # Overall status with large indicator
    status = health.get("status", "unknown")
    status_colors = {"healthy": "green", "degraded": "yellow", "unhealthy": "red"}
    status_icons = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}
    color = status_colors.get(status, "white")
    icon = status_icons.get(status, "❓")
    
    # Create overall health panel
    health_text = f"[bold {color}]{icon} SYSTEM STATUS: {status.upper()}[/bold {color}]"
    console.print(Panel(
        health_text,
        border_style=color,
        padding=(1, 2),
        title="[bold white]🏥 System Health[/bold white]"
    ))
    console.print()
    
    # Create detailed components table
    components_table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        title="[bold cyan]🔧 Components Status[/bold cyan]",
        box=None
    )
    components_table.add_column("Component", style="bold white", width=25)
    components_table.add_column("Status", width=20)
    components_table.add_column("Details", style="dim", overflow="fold")
    
    # Components
    for name, comp in health.get("components", {}).items():
        comp_status = comp.get("status", "unknown")
        comp_colors = {"healthy": "green", "degraded": "yellow", "unhealthy": "red"}
        comp_icons = {"healthy": "●", "degraded": "◐", "unhealthy": "○"}
        c = comp_colors.get(comp_status, "white")
        ic = comp_icons.get(comp_status, "?")
        
        # Component icon mapping
        component_icons = {
            "backend": "🔌",
            "playwright": "🎭",
            "database": "🗄️",
            "cache": "💾",
            "llm": "🧠"
        }
        component_icon = component_icons.get(name.lower(), "⚙️")
        
        components_table.add_row(
            f"{component_icon} {name.title()}",
            f"[{c}]{ic} {comp_status.upper()}[/{c}]",
            comp.get("message", "Running normally")
        )
    
    console.print(components_table)
    
    # Timestamp info
    if health.get("timestamp"):
        console.print()
        console.print(Panel(
            f"[dim]Last updated: {health['timestamp']}[/dim]",
            border_style="dim",
            padding=(0, 2)
        ))

# ========== MAIN LOOP ==========

def interactive_mode():
    """Main interactive loop with enhanced UI"""
    while True:
        choice = show_main_menu()
        
        if choice == "0":
            # Enhanced exit message
            console.print()
            goodbye_panel = Panel(
                "[bold cyan]Thank you for using URWA Brain! 👋[/bold cyan]\n\n"
                "[dim]Autonomous Web Research Agent shutting down...[/dim]",
                border_style="cyan",
                title="[bold red]🚪 Goodbye[/bold red]",
                padding=(1, 2)
            )
            console.print(goodbye_panel)
            console.print()
            break
        
        try:
            console.print()
            
            if choice == "1":
                # Master AI Mode - THE SMART ONE
                console.print(Panel(
                    "[bold yellow]🤖 Master AI Mode[/bold yellow]\n[dim]Tell me anything - I'll figure out what you need![/dim]\n\n"
                    "[dim italic]Examples:[/dim italic]\n"
                    "[dim]• Compare these two Amazon products...[/dim]\n"
                    "[dim]• Scrape this URL and give insights...[/dim]\n"
                    "[dim]• Find me 50 companies with low prices...[/dim]\n"
                    "[dim]• What's the latest news on AI?[/dim]",
                    border_style="yellow",
                    padding=(1, 2)
                ))
                console.print()
                query = Prompt.ask("[bold yellow]┃[/bold yellow] [bold white]What would you like me to do?[/bold white]")
                if query.strip():
                    asyncio.run(master_ai_handler(query))
            
            elif choice == "2":
                # Chat Mode
                console.print(Panel(
                    "[bold white]💬 Chat Mode[/bold white]\n[dim]Ask me anything and get AI-powered answers[/dim]",
                    border_style="cyan",
                    padding=(0, 2)
                ))
                console.print()
                query = Prompt.ask("[bold cyan]┃[/bold cyan] [bold white]Your question[/bold white]")
                if query.strip():
                    asyncio.run(chat_mode_handler(query))
            
            elif choice == "3":
                # Deep Research
                console.print(Panel(
                    "[bold white]📚 Deep Research Mode[/bold white]\n[dim]Comprehensive multi-source analysis[/dim]",
                    border_style="magenta",
                    padding=(0, 2)
                ))
                console.print()
                query = Prompt.ask("[bold magenta]┃[/bold magenta] [bold white]Research topic[/bold white]")
                if query.strip():
                    asyncio.run(deep_research_handler(query))
            
            elif choice == "4":
                # Scraper
                console.print(Panel(
                    "[bold white]🕷️ Scraper Tool[/bold white]\n[dim]Extract content from any website[/dim]",
                    border_style="cyan",
                    padding=(0, 2)
                ))
                console.print()
                url = Prompt.ask("[bold cyan]┃[/bold cyan] [bold white]Target URL[/bold white]")
                if url.strip():
                    asyncio.run(scraper_handler(url))
            
            elif choice == "5":
                # Site Analyzer
                console.print(Panel(
                    "[bold white]🔍 Site Analyzer[/bold white]\n[dim]Analyze website protection and structure[/dim]",
                    border_style="magenta",
                    padding=(0, 2)
                ))
                console.print()
                url = Prompt.ask("[bold magenta]┃[/bold magenta] [bold white]URL to analyze[/bold white]")
                if url.strip():
                    asyncio.run(site_analyzer_handler(url))
            
            elif choice == "6":
                # System Status
                console.print(Panel(
                    "[bold white]📊 System Status[/bold white]\n[dim]Monitor system health and metrics[/dim]",
                    border_style="cyan",
                    padding=(0, 2)
                ))
                console.print()
                asyncio.run(system_status_handler())
        
        except KeyboardInterrupt:
            console.print("\n")
            console.print(Panel(
                "[yellow]⚠️ Operation cancelled by user[/yellow]",
                border_style="yellow",
                padding=(0, 2)
            ))
        except Exception as e:
            console.print("\n")
            console.print(Panel(
                f"[bold red]❌ Error[/bold red]\n\n[white]{str(e)}[/white]",
                border_style="red",
                title="Error Details",
                padding=(1, 2)
            ))
        
        # Enhanced return prompt
        console.print()
        console.print("[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]")
        Prompt.ask("[bold cyan]┃[/bold cyan] [dim]Press Enter to return to menu[/dim]", default="")
        console.clear()
        print_banner()

async def site_analyzer_handler(url: str):
    """Analyze site protection and structure"""
    console.print(f"\n[cyan]Analyzing: {url}[/cyan]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[dim]Profiling site...[/dim]", total=None)
        
        result = await call_api("/api/v1/strategy/profile-site", method="GET", params={"url": url})
        
        progress.stop()
    
    console.print()
    
    if result.get("status") == "success" and result.get("profile"):
        prof = result["profile"]
        
        # Display analysis table
        table = Table(title="Site Analysis", border_style="cyan")
        table.add_column("Property", style="bold")
        table.add_column("Value")
        
        risk = prof.get("risk_level", "unknown")
        risk_colors = {"low": "[green]", "medium": "[yellow]", "high": "[red]", "extreme": "[bold red]"}
        risk_color = risk_colors.get(risk, "")
        
        table.add_row("Risk Level", f"{risk_color}{risk.upper()}[/]")
        table.add_row("Protection", prof.get("protection", "Unknown"))
        table.add_row("Needs JavaScript", "Yes" if prof.get("needs_rendering") else "No")
        table.add_row("Recommended Strategy", prof.get("recommended_strategy", "stealth"))
        table.add_row("Can Scrape", "[green]✓ Yes[/]" if risk in ["low", "medium"] else "[yellow]⚠ Difficult[/]")
        
        console.print(table)
    else:
        console.print(Panel(f"[yellow]{result.get('message', 'Analysis failed')}[/yellow]", border_style="yellow"))

async def system_status_handler():
    """Display system health and metrics"""
    console.print("[cyan]Fetching system status...[/cyan]")
    
    health = await call_api("/api/v1/system/health", method="GET")
    
    if health.get("status") == "error":
        console.print(Panel(f"[red]{health.get('message')}[/red]", border_style="red"))
        return
    
    # Create status table
    table = Table(title="System Status", border_style="cyan")
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Details")
    
    # Overall status
    status = health.get("status", "unknown")
    color = "green" if status == "healthy" else "yellow" if status == "degraded" else "red"
    table.add_row("Overall Health", f"[{color}]{status.upper()}[/{color}]", "")
    
    # Components
    for name, comp in health.get("components", {}).items():
        comp_status = comp.get("status", "unknown")
        c = "green" if comp_status == "healthy" else "yellow" if comp_status == "degraded" else "red"
        table.add_row(f"  - {name}", f"[{c}]{comp_status}[/{c}]", comp.get("message", ""))
    
    # Uptime
    if health.get("timestamp"):
        table.add_row("Timestamp", "", health["timestamp"])
    
    console.print(table)

# ========== MAIN LOOP ==========

def interactive_mode():
    """Main interactive loop"""
    while True:
        choice = show_main_menu()
        
        if choice == "0":
            console.print("\n[red][-] Exiting...[/red]")
            break
        
        try:
            if choice == "1":
                # Chat Mode
                console.print("\n[yellow][*] Loading CHAT module...[/yellow]")
                query = Prompt.ask("[green][?] Ask me anything[/green]")
                if query.strip():
                    asyncio.run(chat_mode_handler(query))
            
            elif choice == "2":
                # Deep Research
                console.print("\n[yellow][*] Loading RESEARCH module...[/yellow]")
                query = Prompt.ask("[green][?] What should I research?[/green]")
                if query.strip():
                    asyncio.run(deep_research_handler(query))
            
            elif choice == "3":
                # Scraper
                console.print("\n[yellow][*] Loading SCRAPER module...[/yellow]")
                url = Prompt.ask("[green][?] Enter URL to scrape[/green]")
                if url.strip():
                    asyncio.run(scraper_handler(url))
            
            elif choice == "4":
                # Site Analyzer
                console.print("\n[yellow][*] Loading ANALYZER module...[/yellow]")
                url = Prompt.ask("[green][?] Enter URL to analyze[/green]")
                if url.strip():
                    asyncio.run(site_analyzer_handler(url))
            
            elif choice == "5":
                # System Status
                asyncio.run(system_status_handler())
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
        
        # Return to menu
        console.print("\n[dim]Press Enter to return...[/dim]")
        input()
        console.clear()
        print_banner()

def main():
    """Main entry point"""
    console.clear()
    print_banner()
    
    # Check services
    check_services()
    
    # Start interactive mode
    interactive_mode()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[cyan]Goodbye! 👋[/cyan]")
        sys.exit(0)
    except Exception as e:
        # Print error without markup to avoid Rich formatting issues
        console.print("\n[red]Fatal Error:[/red]")
        console.print(str(e), style="red", markup=False)
        sys.exit(1)
