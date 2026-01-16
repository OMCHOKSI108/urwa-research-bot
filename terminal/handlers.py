
async def strategy_stats_handler():
    """Display comprehensive strategy statistics with visualization"""
    
    # Fetch stats
    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[bold cyan]Fetching strategy intelligence...[/bold cyan]"),
        transient=True
    ) as progress:
        task = progress.add_task("fetching", total=None)
        
        # Fetch both scraper stats and strategy engine stats
        scraper_stats = await call_api("/api/v1/scraper-stats", method="GET")
        strategy_stats = await call_api("/api/v1/strategy/stats", method="GET")
        
    console.print(Panel(
        "[bold cyan]📊 Strategy Performance Dashboard[/bold cyan]", 
        border_style="cyan",
        subtitle="[dim]Real-time scraping intelligence[/dim]"
    ))
    console.print()

    # 1. Strategy Comparison Table
    if scraper_stats.get("status") == "success":
        strategies = scraper_stats.get("strategies", {})
        
        table = Table(
            title="[bold white]Strategy Success Rates[/bold white]",
            border_style="dim",
            header_style="bold magenta",
            box=None
        )
        table.add_column("Strategy", style="cyan")
        table.add_column("Description", style="dim white")
        table.add_column("Successes", justify="right", style="green")
        table.add_column("Rate", justify="right", style="bold yellow")
        
        for key, data in strategies.items():
            name = data.get("name", key)
            desc = data.get("description", "")
            count = data.get("success_count", 0)
            rate = data.get("success_rate", "0%")
            
            # Color code the rate
            rate_val = float(rate.strip('%'))
            rate_style = "green" if rate_val > 80 else "yellow" if rate_val > 50 else "red"
            
            table.add_row(name, desc, str(count), f"[{rate_style}]{rate}[/{rate_style}]")
            
        console.print(table)
        console.print()
        
        # Overall totals
        totals = scraper_stats.get("totals", {})
        grid = Table.grid(padding=(0, 4))
        grid.add_column(justify="center", style="bold white")
        grid.add_column(justify="center", style="bold white")
        grid.add_column(justify="center", style="bold white")
        
        grid.add_row(
            f"[bold cyan]{totals.get('total_requests', 0)}[/bold cyan]\nTotal Requests",
            f"[bold green]{totals.get('overall_success_rate', '0%')}[/bold green]\nOverall Success",
            f"[bold red]{totals.get('total_failures', 0)}[/bold red]\nFailures"
        )
        console.print(Panel(grid, border_style="dim"))
        console.print()

    # 2. Learning Insights
    if strategy_stats.get("status") == "success":
        stats = strategy_stats.get("stats", {})
        learning = stats.get("learning", {})
        
        if learning:
            console.print("[bold yellow]🧠 Adaptive Learning Insights[/bold yellow]")
            
            # Show top learned domains
            domain_table = Table(show_header=True, header_style="bold white", border_style="dim", box=None)
            domain_table.add_column("Domain", style="cyan")
            domain_table.add_column("Best Strategy", style="green")
            domain_table.add_column("Success Rate", justify="right")
            
            count = 0
            for domain, data in learning.items():
                if count >= 5: break
                best = data.get("best_strategy", "unknown")
                rate = f"{data.get('success_rate', 0)*100:.0f}%"
                domain_table.add_row(domain, best, rate)
                count += 1
            
            if count > 0:
                console.print(domain_table)
            else:
                console.print("[dim]No learning data yet. Start scraping to train the AI![/dim]")

    console.print()
    Prompt.ask("[dim]Press Enter to return to menu...[/dim]")

def settings_handler():
    """Handle settings configuration with easy toggles"""
    global USE_OLLAMA
    
    while True:
        console.clear()
        console.print(Panel(
            "[bold white]⚙️  Settings & Configuration[/bold white]",
            border_style="cyan"
        ))
        console.print()
        
        # Display current settings
        settings_table = Table(show_header=True, header_style="bold magenta", box=None)
        settings_table.add_column("Setting", style="bold white")
        settings_table.add_column("State", style="bold")
        settings_table.add_column("Description", style="dim")
        
        ollama_state = "[green]ON (Local AI)[/green]" if USE_OLLAMA else "[yellow]OFF (Cloud AI)[/yellow]"
        settings_table.add_row(
            "[1] AI Provider", 
            ollama_state, 
            "Toggle between Cloud (Gemini/Groq) and Local (Ollama)"
        )
        
        console.print(settings_table)
        console.print()
        console.print("[dim]Enter the number to toggle setting, or 0 to return[/dim]")
        
        choice = Prompt.ask("Select option", choices=["1", "0"], default="0")
        
        if choice == "0":
            break
        elif choice == "1":
            # Check availability before enabling
            if not USE_OLLAMA:
                try:
                    resp = requests.get("http://localhost:11434/api/tags", timeout=1)
                    if resp.status_code == 200:
                        USE_OLLAMA = True
                        console.print("[green]✅ Switched to Local Ollama AI[/green]")
                    else:
                        console.print("[red]❌ Ollama is not running on localhost:11434[/red]")
                except:
                    console.print("[red]❌ Ollama is not detected[/red]")
                    console.print("[dim]Make sure 'ollama serve' is running[/dim]")
                time.sleep(1.5)
            else:
                USE_OLLAMA = False
                console.print("[yellow]⚡ Switched to Cloud AI (Gemini/Groq)[/yellow]")
                time.sleep(1)

# Interactive looping Master AI
async def interactive_master_ai():
    """Continuous conversation loop with the unified agent"""
    console.print(Panel(
        "[bold green]🤖 Master AI Console[/bold green]\n"
        "[dim]Talk naturally. Type 'exit' to quit, 'clear' to reset.[/dim]",
        border_style="green"
    ))
    
    # Get history first
    history_resp = await call_api("/api/v1/agent/history", method="GET")
    history_len = 0
    if history_resp.get("status") == "success":
        history_len = len(history_resp.get("history", []))
        if history_len > 0:
            console.print(f"[dim]Loaded {history_len} previous messages[/dim]")
    
    while True:
        try:
            query = Prompt.ask("\n[bold cyan]You[/bold cyan]")
            
            if not query:
                continue
                
            if query.lower() in ["exit", "quit", "menu"]:
                break
            
            if query.lower() in ["clear", "reset"]:
                await call_api("/api/v1/agent/clear", method="POST")
                console.print("[dim]Conversation history cleared[/dim]")
                continue
                
            # Reuse the master logic but in-line
            await master_ai_handler(query)
            
        except KeyboardInterrupt:
            break
