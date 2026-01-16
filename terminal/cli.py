"""
URWA Brain - Terminal CLI
Beautiful command-line interface for URWA Brain AI Agent
"""

import sys
import time
import asyncio
import subprocess
import argparse
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Union

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")

# --- Dependencies ---
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.live import Live
    from rich import print as rprint
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
    from rich.live import Live
    from rich import print as rprint
    import aiohttp
    import requests

console = Console()

class Config:
    API_URL = "http://localhost:8000"
    OLLAMA_URL = "http://localhost:11434"
    USE_OLLAMA = False
    
class URWAClient:
    """Robust API Client"""
    
    @staticmethod
    async def request(endpoint: str, method: str = "POST", params: dict = None, timeout: int = 300) -> Dict[str, Any]:
        url = f"{Config.API_URL}{endpoint}"
        if params:
            # Clean bools
            params = {k: str(v).lower() if isinstance(v, bool) else v for k, v in params.items()}
            
        try:
            async with aiohttp.ClientSession() as session:
                kwargs = {"params": params, "timeout": aiohttp.ClientTimeout(total=timeout)}
                
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
            return {"status": "error", "message": f"Could not connect to backend at {Config.API_URL}. Is it running?"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

def print_banner():
    # Clearer 'Standard' Font ASCII Banner
    console.print(r"""[bold cyan]
   __  ______ _       _____ 
  / / / / __ \ |     / /   |
 / / / / /_/ / | /| / / /| |
/ /_/ / _, _/| |/ |/ / ___ |
\____/_/ |_| |__/|__/_/  |_|
                            
      [red]v3.5[/red]
    [/bold cyan]""")
    
    console.print("[dim]   [+] Tool Created by URWA Team (AI Agent)[/dim]")
    console.print()

def start_backend():
    """Start the backend server in a new window/tab"""
    console.print("[yellow]Starting backend server...[/yellow]")
    backend_dir = Path(__file__).parent.parent / "backend"
    
    if sys.platform == "win32":
        cmd = f'start "URWA Backend" /min cmd /k "cd /d {backend_dir} && ..\\venv\\Scripts\\activate && uvicorn app.main:app --reload"'
        os.system(cmd)
    else:
        # Linux/Mac
        cmd = f"cd {backend_dir} && ../venv/bin/uvicorn app.main:app --reload"
        subprocess.Popen(cmd, shell=True, start_new_session=True)
    
    console.print("[dim]Waiting for server to initialize...[/dim]")
    
    # Wait for health check
    for _ in range(10):
        try:
            requests.get(f"{Config.API_URL}/health", timeout=1)
            console.print("[green]Backend Online![/green]")
            return True
        except:
            time.sleep(2)
            
    return False

def check_services():
    # Check Backend
    try:
        requests.get(f"{Config.API_URL}/health", timeout=1)
        console.print("[green]✔ Backend is Online[/green]")
    except:
        console.print("[red]✘ Backend is Offline[/red]")
        if Confirm.ask("Start Backend Server?"):
            start_backend()
            
    # Check Ollama
    try:
        requests.get(f"{Config.OLLAMA_URL}", timeout=1)
        Config.USE_OLLAMA = True
        console.print("[green]✔ Ollama Detected[/green]")
    except:
        console.print("[yellow]⚠ Ollama Not Detected (Using Cloud Fallback)[/yellow]")

async def execute_task(task_type: str, query: str):
    """Execute a task with nice UI"""
    endpoint_map = {
        "chat": "/api/v1/research",     # Unified Research Chat
        "research": "/api/v1/research", # Deep research
        "scrape": "/api/v1/agent",      # Unified Agent (can handle specific scrape requests)
        "analyze": "/api/v1/agent"      # Unified Agent
    }
    
    endpoint = endpoint_map.get(task_type, "/api/v1/agent")
    
    # Params setup
    params = {"use_ollama": Config.USE_OLLAMA}
    
    if task_type == "research":
        params.update({"query": query, "deep": True})
    elif task_type == "chat":
        params.update({"query": query, "deep": False})
    else:
        # Identify as agent prompt
        prefix = "scrape" if task_type == "scrape" else "analyze" 
        if not query.lower().startswith(prefix):
            query = f"{prefix} {query}"
        params.update({"input": query})
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"[dim]Executing {task_type}...[/dim]", total=None)
        result = await URWAClient.request(endpoint, params=params)
        progress.update(task, completed=True)
        
    # Render Output
    console.print()
    if result.get("status") == "error":
        console.print(f"[red]Error:[/red] {result.get('message')}")
        return

    # Intelligent Parsing based on Result Structure
    
    # 1. Direct Answer (Research/Chat)
    if result.get("answer"):
        console.print(Panel(Markdown(result["answer"]), title="Result", border_style="green"))
        
        if result.get("sources"):
            console.print("\n[bold]Sources:[/bold]")
            for src in result["sources"][:5]:
                console.print(f"- [link={src.get('url')}]{src.get('title') or src.get('url')}[/link]")
                
    # 2. Agent Result (Scrape/Analyze)
    elif result.get("result"):
        res_data = result["result"]
        
        # If it's structured data
        if res_data.get("extracted_data"):
            console.print(Panel(Markdown(str(res_data["extracted_data"])), title="Extracted Data", border_style="cyan"))
        
        # If it's just raw content
        elif res_data.get("content"):
            content = res_data["content"]
            if len(content) > 1000:
                 content = content[:1000] + "\n...(truncated)..."
            console.print(Panel(content, title="Extracted Content", border_style="cyan"))
            
        # Analysis result
        elif res_data.get("analysis"):
             console.print(Panel(Markdown(res_data["analysis"]), title="Analysis", border_style="magenta"))
             
    # 3. Fallback
    else:
        console.print(result)

async def system_status():
    """Show system health stats"""
    console.print("[cyan]Fetching system status...[/cyan]")
    
    health = await URWAClient.request("/api/v1/system/health", method="GET")
    metrics = await URWAClient.request("/api/v1/system/metrics", method="GET")
    
    table = Table(title="System Status")
    table.add_column("Component")
    table.add_column("Status")
    table.add_column("Details")
    
    # Health
    status = health.get("status", "unknown")
    color = "green" if status == "healthy" else "red"
    table.add_row("Overall Health", f"[{color}]{status.upper()}[/{color}]", "")
    
    # Components
    for name, comp in health.get("components", {}).items():
        comp_status = comp.get("status", "unknown")
        c = "green" if comp_status == "healthy" else "red"
        table.add_row(f"  - {name}", f"[{c}]{comp_status}[/{c}]", comp.get("message", ""))
        
    # Metrics
    if metrics.get("uptime_seconds"):
        uptime = round(metrics["uptime_seconds"] / 3600, 2)
        table.add_row("Uptime", "", f"{uptime} hours")
        
    console.print(table)

def interactive_mode():
    """Main Menu Loop"""
    while True:
        console.print("[bold cyan][::] Select An Action For Your Agent [::][/bold cyan]\n")
        
        # Grid Menu Style
        console.print("""
[bold white][01][/bold white] [cyan]Chat Mode[/cyan]        [bold white][04][/bold white] [cyan]Site Analyzer[/cyan]
[bold white][02][/bold white] [cyan]Deep Research[/cyan]    [bold white][05][/bold white] [cyan]System Status[/cyan]
[bold white][03][/bold white] [cyan]Scraper Tool[/cyan]     [bold white][00][/bold white] [cyan]Exit[/cyan]
        """)
        
        choice = Prompt.ask("[bold cyan][::] Select Option[/bold cyan]", choices=["01", "1", "02", "2", "03", "3", "04", "4", "05", "5", "00", "0"], default="01")
        
        # Normalize choice (01 -> 1)
        if choice.startswith("0") and len(choice) > 1:
            choice = choice[1]
            
        if choice == "0":
            console.print("\n[red][-] Exiting...[/red]")
            sys.exit(0)
            
        elif choice == "5":
            asyncio.run(system_status())
            
            # Pause effect
            console.print("\nPress Enter to return...")
            input()
            console.clear()
            print_banner()
            continue
            
        task_map = {"1": "chat", "2": "research", "3": "scrape", "4": "analyze"}
        task = task_map.get(choice, "chat")
        
        q_prompt = {
            "chat": "Ask me anything",
            "research": "What should I research?",
            "scrape": "Enter URL to scrape",
            "analyze": "Enter URL to analyze"
        }
        
        console.print(f"\n[yellow][*] Loading {task.upper()} module...[/yellow]")
        query = Prompt.ask(f"[green][?] {q_prompt[task]}[/green]")
        asyncio.run(execute_task(task, query))
        
        # Return to menu logic
        console.print("\nPress Enter to return...")
        input()
        console.clear()
        print_banner()

def main():
    # Handle "urwa sans start" arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("args", nargs="*", help="Arguments")
    args = parser.parse_args()
    
    # Check for specific command signature "sans start" or just run smoothly
    if len(args.args) >= 1:
        # If user typed 'urwa sans start', args might be ['sans', 'start']
        # We just proceed. 
        pass

    console.clear()
    print_banner()
    
    check_services()
    
    # Interactive Mode
    interactive_mode()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")



def chat_mode():
    """Interactive chat mode."""
    console.print("\n[bold cyan]═══ CHAT MODE ═══[/bold cyan]")
    console.print("[dim]Type your questions. Type 'exit' to go back to menu.[/dim]\n")
    
    while True:
        try:
            query = Prompt.ask("[bold green]You[/bold green]")
            
            if query.lower() in ['exit', 'quit', 'q', 'back']:
                break
            
            if not query.strip():
                continue
            
            # Run the query
            asyncio.run(run_agent_query(query, mode="chat"))
            console.print()
            
        except KeyboardInterrupt:
            break
    
    console.print("[yellow]Exiting chat mode...[/yellow]")


def scrape_mode():
    """URL scraping mode - Full power with protected site support."""
    console.print("\n[bold cyan]═══ SCRAPE MODE ═══[/bold cyan]")
    console.print("[dim]Enter a URL to scrape. Supports protected sites with advanced bypass.[/dim]")
    console.print("[dim]Type 'exit' to go back.[/dim]\n")
    
    url = Prompt.ask("[bold green]URL[/bold green]")
    
    if url.lower() in ['exit', 'quit', 'q']:
        return
    
    instruction = Prompt.ask(
        "[bold green]What to extract[/bold green]",
        default="Extract all main content"
    )
    
    # Use the protected-scrape endpoint for full power
    console.print(f"\n[cyan]Scraping with full power: {url}[/cyan]\n")
    
    use_ollama = os.environ.get("USE_OLLAMA") == "true"
    
    async def do_scrape():
        import aiohttp
        
        base_url = "http://localhost:8000"
        
        # Convert booleans to strings
        params = {
            "url": url,
            "instruction": instruction
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # First, profile the site to show protection level
                console.print("[dim]Analyzing site protection...[/dim]")
                
                async with session.get(
                    f"{base_url}/api/v1/strategy/profile-site",
                    params={"url": url},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    profile = await resp.json()
                    
                    risk = profile.get("risk", "unknown")
                    protection = profile.get("protection", "none")
                    strategy = profile.get("recommended_strategy", "stealth")
                    
                    risk_colors = {"low": "green", "medium": "yellow", "high": "red", "extreme": "bold red"}
                    color = risk_colors.get(risk, "white")
                    
                    console.print(f"  Risk Level: [{color}]{risk.upper()}[/{color}]")
                    console.print(f"  Protection: {protection}")
                    console.print(f"  Strategy: {strategy}")
                    console.print()
                
                # Now do the actual scrape with protected-scrape endpoint
                console.print("[dim]Scraping with advanced bypass...[/dim]")
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TimeElapsedColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task("[cyan]Scraping...", total=None)
                    
                    async with session.post(
                        f"{base_url}/api/v1/protected-scrape",
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=180)
                    ) as resp:
                        result = await resp.json()
                    
                    progress.update(task, description="[green]Complete!")
                
                # Display results
                console.print()
                
                if result.get("status") == "success":
                    console.print(Panel("[green]Scrape Successful![/green]", border_style="green"))
                    
                    # Content can be in result.result.content OR result.content
                    content = None
                    res = result.get("result", {})
                    
                    # Check nested result first
                    if res and res.get("content"):
                        content = res["content"]
                    # Check top-level content (from fallback scraping)
                    elif result.get("content"):
                        content = result["content"]
                    
                    if content:
                        console.print("\n[bold cyan]Scraped Content:[/bold cyan]\n")
                        if len(content) > 3000:
                            content = content[:3000] + "\n\n[dim]... (truncated, full content available via API)[/dim]"
                        console.print(Markdown(content))
                    
                    # Show message if available
                    if result.get("message"):
                        console.print(f"\n[dim]{result['message']}[/dim]")
                    
                    # Show structured data if available
                    if res and res.get("structured_data"):
                        console.print("\n[bold cyan]Structured Data:[/bold cyan]")
                        console.print(f"{res['structured_data']}")
                    
                    # Show entities if available
                    if res and res.get("entities"):
                        console.print("\n[bold cyan]Entities Found:[/bold cyan]")
                        for entity in res["entities"][:10]:
                            console.print(f"  • {entity.get('name', entity.get('title', 'N/A'))}")
                    
                    console.print(f"\n[dim]Content length: {result.get('content_length', len(content) if content else 0)} characters[/dim]")
                else:
                    console.print(Panel(f"[yellow]Status: {result.get('status', 'unknown')}[/yellow]", border_style="yellow"))
                    if result.get("message"):
                        console.print(f"[dim]{result['message']}[/dim]")
                    
                    # Suggest alternatives
                    console.print("\n[bold cyan]Suggestions:[/bold cyan]")
                    console.print("  • Try a more specific URL (e.g., /list-of-companies instead of homepage)")
                    console.print("  • Use Chat Mode to research the topic instead")
                    console.print("  • Some sites require authentication")
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    asyncio.run(do_scrape())


def research_mode():
    """Deep research mode."""
    console.print("\n[bold cyan]═══ RESEARCH MODE ═══[/bold cyan]")
    console.print("[dim]Enter your research topic. Type 'exit' to go back.[/dim]\n")
    
    topic = Prompt.ask("[bold green]Research Topic[/bold green]")
    
    if topic.lower() in ['exit', 'quit', 'q']:
        return
    
    asyncio.run(run_agent_query(topic, mode="research"))


def fact_check_mode():
    """Fact checking mode."""
    console.print("\n[bold cyan]═══ FACT CHECK MODE ═══[/bold cyan]")
    console.print("[dim]Enter a claim to verify. Type 'exit' to go back.[/dim]\n")
    
    claim = Prompt.ask("[bold green]Claim to verify[/bold green]")
    
    if claim.lower() in ['exit', 'quit', 'q']:
        return
    
    query = f"Is it true that {claim}"
    asyncio.run(run_agent_query(query, mode="fact_check"))


def site_analysis_mode():
    """Site analysis mode - Full protection profiling."""
    console.print("\n[bold cyan]═══ SITE ANALYSIS MODE ═══[/bold cyan]")
    console.print("[dim]Analyze any site for protection level and scraping difficulty.[/dim]")
    console.print("[dim]Type 'exit' to go back.[/dim]\n")
    
    url = Prompt.ask("[bold green]URL to analyze[/bold green]")
    
    if url.lower() in ['exit', 'quit', 'q']:
        return
    
    async def do_analysis():
        import aiohttp
        
        base_url = "http://localhost:8000"
        
        console.print(f"\n[cyan]Analyzing: {url}[/cyan]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Profiling site...", total=None)
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{base_url}/api/v1/strategy/profile-site",
                        params={"url": url},
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as resp:
                        result = await resp.json()
                
                progress.update(task, description="[green]Complete!")
                
            except Exception as e:
                progress.update(task, description="[red]Failed!")
                console.print(f"[red]Error: {e}[/red]")
                return
        
        console.print()
        
        # Display comprehensive analysis
        risk = result.get("risk", "unknown")
        risk_colors = {"low": "green", "medium": "yellow", "high": "red", "extreme": "bold red"}
        color = risk_colors.get(risk, "white")
        
        console.print(Panel(
            f"[bold]Site Analysis: {url}[/bold]",
            title="Protection Profile",
            border_style=color.replace("bold ", "")
        ))
        
        console.print(f"\n  [bold]Risk Level:[/bold] [{color}]{risk.upper()}[/{color}]")
        console.print(f"  [bold]Protection:[/bold] {result.get('protection', result.get('bot_wall', 'none'))}")
        console.print(f"  [bold]Bot Wall Detected:[/bold] {result.get('bot_wall', 'none')}")
        console.print(f"  [bold]Needs JavaScript:[/bold] {'Yes' if result.get('needs_rendering') else 'No'}")
        console.print(f"  [bold]Recommended Strategy:[/bold] {result.get('recommended_strategy', 'stealth')}")
        
        can_scrape = risk in ["low", "medium"]
        console.print(f"  [bold]Can Scrape:[/bold] {'[green]✓ Yes[/green]' if can_scrape else '[yellow]⚠ Difficult[/yellow]'}")
        
        # Show details if available
        details = result.get("details", {})
        if details:
            console.print(f"\n[bold cyan]Details:[/bold cyan]")
            for key, value in details.items():
                if key != "warnings":
                    console.print(f"  • {key}: {value}")
        
        # Warnings
        warnings = details.get("warnings", []) if details else []
        if warnings:
            console.print(f"\n[bold yellow]Warnings:[/bold yellow]")
            for warning in warnings:
                console.print(f"  ⚠ {warning}")
        
        # Recommendations
        console.print(f"\n[bold cyan]Recommendations:[/bold cyan]")
        strategy = result.get('recommended_strategy', 'stealth')
        if strategy == "lightweight":
            console.print("  ✓ This site can be scraped easily with simple HTTP requests")
        elif strategy == "stealth":
            console.print("  ⚠ Use Playwright stealth mode for best results")
        elif strategy == "ultra_stealth":
            console.print("  ⚠ Heavy protection detected - use Ultra Stealth mode")
            console.print("  ⚠ May require multiple attempts or human intervention")
        
        console.print()
    
    asyncio.run(do_analysis())


def system_status_mode():
    """System status dashboard."""
    while True:
        console.print("\n[bold cyan]═══ SYSTEM STATUS ═══[/bold cyan]")
        console.print("[dim]Monitor API health, stats, and costs.[/dim]\n")
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_row("[1] System Health", "[4] Cost & Usage")
        table.add_row("[2] Scraper Stats", "[5] Circuit Breakers")
        table.add_row("[3] Strategy Metrics", "[6] Recent Logs")
        table.add_row("[0] Back to Main Menu", "")
        
        console.print(table)
        
        choice = Prompt.ask("\n[bold green]Select Option[/bold green]", choices=["0", "1", "2", "3", "4", "5", "6"], default="1")
        
        if choice == "0":
            break
            
        async def fetch_status():
            console.print()
            try:
                if choice == "1":
                    res = await call_api("/api/v1/system/health", method="GET")
                    console.print_json(data=res)
                elif choice == "2":
                    res = await call_api("/api/v1/scraper-stats", method="GET")
                    console.print_json(data=res)
                elif choice == "3":
                    res = await call_api("/api/v1/strategy/stats", method="GET")
                    console.print_json(data=res)
                elif choice == "4":
                    res = await call_api("/api/v1/system/cost", method="GET")
                    console.print_json(data=res)
                elif choice == "5":
                    res = await call_api("/api/v1/system/circuits", method="GET")
                    console.print_json(data=res)
                elif choice == "6":
                    res = await call_api("/api/v1/system/logs", params={"limit": 10}, method="GET")
                    console.print_json(data=res)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")

        asyncio.run(fetch_status())


def advanced_tools_mode():
    """Advanced tools and utilities."""
    while True:
        console.print("\n[bold cyan]═══ ADVANCED TOOLS ═══[/bold cyan]")
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_row("[1] Browser Profiles", "[4] Compliance Check")
        table.add_row("[2] Human Task Queue", "[5] Clear Scraper Cache")
        table.add_row("[3] Data Normalizer", "[6] Reset Strategy AI")
        table.add_row("[0] Back to Main Menu", "")
        
        console.print(table)
        
        choice = Prompt.ask("\n[bold green]Select Option[/bold green]", choices=["0", "1", "2", "3", "4", "5", "6"], default="1")
        
        if choice == "0":
            break
            
        async def run_tool():
            console.print()
            try:
                if choice == "1":
                    res = await call_api("/api/v1/browser-profiles", method="GET")
                    console.print_json(data=res)
                elif choice == "2":
                    res = await call_api("/api/v1/human-queue", method="GET")
                    console.print_json(data=res)
                elif choice == "3":
                    console.print("[dim]Normalize data into structured formats.[/dim]")
                    dtype = Prompt.ask("Data Type", choices=["price", "date", "location", "company", "rating", "phone"])
                    val = Prompt.ask("Raw Value")
                    res = await call_api("/api/v1/normalize", params={"data_type": dtype, "value": val}, method="POST")
                    console.print_json(data=res)
                elif choice == "4":
                    url = Prompt.ask("URL to check")
                    res = await call_api("/api/v1/strategy/compliance-check", params={"url": url}, method="GET")
                    console.print_json(data=res)
                elif choice == "5":
                    if Prompt.ask("Clear scraper cache?", choices=["y", "n"], default="n") == "y":
                        res = await call_api("/api/v1/scraper-cache/clear", method="POST")
                        console.print(f"[green]{res.get('message', 'Done')}[/green]")
                elif choice == "6":
                    if Prompt.ask("Clear ALL strategy learning data? (Resets intelligence)", choices=["y", "n"], default="n") == "y":
                        res = await call_api("/api/v1/strategy/clear", method="POST")
                        console.print(f"[green]{res.get('message', 'Done')}[/green]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")

        asyncio.run(run_tool())


def start_api_server():
    """Start the API server in the current terminal (blocking)."""
    console.print("\n[bold cyan]Starting API Server...[/bold cyan]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")
    
    backend_path = Path(__file__).parent.parent / "backend"
    run_script = backend_path / "run.py"
    
    try:
        subprocess.run([sys.executable, str(run_script)], cwd=str(backend_path))
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped.[/yellow]")


def start_api_server_background():
    """Start API server in a NEW terminal window (non-blocking)."""
    backend_path = Path(__file__).parent.parent / "backend"
    run_script = backend_path / "run.py"
    venv_python = sys.executable
    
    console.print("\n[cyan]Starting API server in a new terminal window...[/cyan]")
    
    if sys.platform == "win32":
        # Windows: Open new cmd window with activated venv
        venv_activate = Path(__file__).parent.parent / "venv" / "Scripts" / "activate.bat"
        cmd = f'start "URWA Brain API Server" cmd /k "cd /d {backend_path} && call {venv_activate} && python run.py"'
        subprocess.Popen(cmd, shell=True, cwd=str(backend_path))
    else:
        # Linux/Mac: Open new terminal
        cmd = f'cd {backend_path} && source ../venv/bin/activate && python run.py'
        # Try different terminal emulators
        terminals = [
            ["gnome-terminal", "--", "bash", "-c", cmd],
            ["xterm", "-e", f"bash -c '{cmd}'"],
            ["konsole", "-e", f"bash -c '{cmd}'"],
        ]
        for term_cmd in terminals:
            try:
                subprocess.Popen(term_cmd)
                break
            except FileNotFoundError:
                continue
    
    # Wait for server to start
    console.print("[dim]Waiting for server to start...[/dim]")
    for i in range(15):  # Wait up to 15 seconds
        time.sleep(1)
        if check_api_server():
            console.print("[green]✓[/green] API Server started successfully!")
            return True
    
    console.print("[red]✗[/red] Server failed to start. Please check the new terminal window for errors.")
    return False


def check_api_server() -> bool:
    """Check if FastAPI server is running."""
    import requests
    try:
        resp = requests.get("http://localhost:8000/health", timeout=3)
        return resp.status_code == 200
    except:
        return False


def main():
    """Main entry point."""
    print_banner()
    
    # System checks
    console.print("\n[bold cyan]System Check[/bold cyan]\n")
    
    if not check_python_version():
        return
    
    # Check virtual environment
    if not check_venv():
        if Confirm.ask("Create virtual environment?", default=True):
            if not create_venv():
                return
            return  # User needs to activate venv
    
    # Check/install requirements
    try:
        from rich.progress import Progress
        console.print("[green]✓[/green] Dependencies available")
    except:
        if Confirm.ask("Install dependencies?", default=True):
            if not install_requirements():
                return
    
    # Check Playwright
    try:
        import playwright
        console.print("[green]✓[/green] Playwright available")
    except:
        if Confirm.ask("Install Playwright browser?", default=True):
            install_playwright()
    
    # Check API Server
    console.print("\n[bold cyan]API Server Check[/bold cyan]\n")
    
    if check_api_server():
        console.print("[green]✓[/green] API Server running at http://localhost:8000")
    else:
        console.print("[yellow]![/yellow] API Server not running")
        console.print("\n[dim]The CLI requires the FastAPI server to be running.[/dim]")
        
        if Confirm.ask("Start API server in a new window?", default=True):
            if not start_api_server_background():
                console.print("[yellow]Please start the API server manually and try again.[/yellow]")
                return
            # Server started, continue to menu
        else:
            console.print("\n[dim]To start manually, open another terminal and run:[/dim]")
            console.print("  [cyan]cd backend[/cyan]")
            console.print("  [cyan]python run.py[/cyan]\n")
            console.print("[yellow]Please start the API server and try again.[/yellow]")
            return
    
    # Show LLM status from API
    try:
        import requests
        resp = requests.get("http://localhost:8000/", timeout=3)
        data = resp.json()
        console.print(f"[green]✓[/green] URWA Brain v{data.get('version', '?')} Online")
    except:
        pass
    
    # LLM Selection
    console.print("\n[bold cyan]LLM Selection[/bold cyan]\n")
    console.print("  [1] Cloud LLM (Gemini/Groq) - Faster, requires API keys")
    console.print("  [2] Local LLM (Ollama) - Private, requires Ollama running")
    
    llm_choice = Prompt.ask("Select LLM", choices=["1", "2"], default="1")
    
    if llm_choice == "2":
        # Check if Ollama is available
        try:
            import requests
            resp = requests.get("http://localhost:11434/api/tags", timeout=5)
            if resp.status_code == 200:
                os.environ["USE_OLLAMA"] = "true"
                console.print("[green]✓[/green] Using Local Ollama LLM")
            else:
                console.print("[yellow]![/yellow] Ollama not responding, using Cloud LLM")
                os.environ["USE_OLLAMA"] = "false"
        except:
            console.print("[yellow]![/yellow] Ollama not available, using Cloud LLM")
            os.environ["USE_OLLAMA"] = "false"
    else:
        os.environ["USE_OLLAMA"] = "false"
        console.print("[green]✓[/green] Using Cloud LLM (Gemini/Groq)")
    
    # Main loop
    while True:
        choice = show_main_menu()
        
        if choice == "0":
            console.print("\n[cyan]Goodbye! 👋[/cyan]\n")
            break
        elif choice == "1":
            chat_mode()
        elif choice == "2":
            scrape_mode()
        elif choice == "3":
            research_mode()
        elif choice == "4":
            fact_check_mode()
        elif choice == "5":
            site_analysis_mode()
        elif choice == "6":
            system_status_mode()
        elif choice == "7":
            advanced_tools_mode()
        elif choice == "8":
            start_api_server()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[cyan]Goodbye! 👋[/cyan]\n")
        sys.exit(0)
