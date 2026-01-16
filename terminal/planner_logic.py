
"""
AUTOMATED RESEARCH PLANNER LOGIC
Splits complex goals into actionable steps and executes them sequentially.
"""
import asyncio
from typing import List, Dict, Any
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class ResearchPlanner:
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.plan_steps = []
        
    async def create_plan(self, goal: str) -> List[Dict]:
        """Generate a structured plan from a high-level goal."""
        
        # In a real scenario, we would ask the LLM to generate this plan.
        # For now, we simulate a robust planning logic based on user intent.
        
        plan = []
        
        # Check intents
        is_fresh = "fresh" in goal.lower() or "latest" in goal.lower() or "news" in goal.lower()
        is_deep = "deep" in goal.lower() or "comprehensive" in goal.lower() or "all" in goal.lower()
        is_entity = "companies" in goal.lower() or "competitors" in goal.lower() or "products" in goal.lower()
        
        # Step 1: Discovery
        plan.append({
            "id": 1,
            "phase": "Discovery",
            "action": "search",
            "description": f"Identify key sources for '{goal}' using multi-engine search.",
            "status": "pending"
        })
        
        # Step 2: Content Acquisition
        if is_entity or is_deep:
            plan.append({
                "id": 2,
                "phase": "Deep Scanning",
                "action": "deep_scrape",
                "description": "Visit up to 20 identified sources and extract structured data.",
                "status": "pending"
            })
        else:
             plan.append({
                "id": 2,
                "phase": "Scraping",
                "action": "scrape",
                "description": "Scrape top 5 most relevant pages for content.",
                "status": "pending"
            })
             
        # Step 3: Synthesis
        plan.append({
            "id": 3,
            "phase": "Analysis",
            "action": "synthesize",
            "description": "Synthesize findings into a final report using LLM.",
            "status": "pending"
        })
        
        self.plan_steps = plan
        return plan

    def display_plan(self):
        """Render the plan to the console."""
        table = Table(title="[bold cyan]📋 Research Plan[/bold cyan]", border_style="cyan")
        table.add_column("ID", style="dim", width=4)
        table.add_column("Phase", style="white")
        table.add_column("Task Description", style="cyan")
        table.add_column("Status", style="yellow")
        
        for step in self.plan_steps:
            status = step['status']
            if status == "pending":
                icon = "○"
                style = "dim"
            elif status == "running":
                icon = "🔄"
                style = "bold yellow"
            elif status == "completed":
                icon = "✅"
                style = "green"
            else:
                icon = "❌"
                style = "red"
                
            table.add_row(
                str(step['id']), 
                step['phase'], 
                step['description'], 
                f"[{style}]{icon} {status}[/{style}]"
            )
            
        console.print(table)
        console.print()

    async def execute_plan(self, client_function_map: Dict[str, Any]):
        """Execute the plan using provided client functions (callbacks)."""
        
        for step in self.plan_steps:
            step['status'] = 'running'
            self.display_plan()
            
            action = step['action']
            
            try:
                # Simulate Delay for UX or Real Work
                await asyncio.sleep(1)
                
                if action == "search":
                    # Call discovery callback
                    if 'search' in client_function_map:
                        await client_function_map['search']()
                
                elif action == "deep_scrape" or action == "scrape":
                    if 'scrape' in client_function_map:
                        await client_function_map['scrape']()
                        
                elif action == "synthesize":
                     if 'synthesize' in client_function_map:
                        await client_function_map['synthesize']()
                
                step['status'] = 'completed'
                # Clear previous table and show updated
                # In a real rich app needed Live display, simplified here
                console.print(f"[green]✓ Step {step['id']} Verified[/green]")
                
            except Exception as e:
                step['status'] = 'failed'
                console.print(f"[red]Step {step['id']} Failed: {e}[/red]")
                break
        
        self.display_plan()
