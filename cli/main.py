#!/usr/bin/env python3
"""
Eigen3 CLI
"""

import os
import sys
import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'functions'))
from service.image import get_image_summary
from service.cost import calculate_cost_from_image_analysis, calculate_and_export_cost_csv
from service.products import catalog

app = typer.Typer(
    name="eigen3-sf",
    help="Eigen3-SF Analysis Tools - Door analysis and plan extraction",
    add_completion=False
)
console = Console()

DOOR_THICKNESS = "1.75\""
INVALID_PATH_MSG = "[red]Invalid file path[/red]"
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}


def _file_path_completer(text: str) -> list[str]:
    """Custom completer for file paths with image file filtering"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        if not text:
            base_path = Path(project_root)
        else:
            if not os.path.isabs(text):
                base_path = Path(project_root) / text
            else:
                base_path = Path(text)
        
        if base_path.is_file() or not base_path.exists():
            base_path = base_path.parent
        
        if base_path.is_dir():
            items = []
            for item in base_path.iterdir():
                try:
                    if item.is_dir():
                        rel_path = str(item.relative_to(project_root)) + "/"
                        items.append(rel_path)
                    elif item.suffix.lower() in IMAGE_EXTENSIONS:
                        rel_path = str(item.relative_to(project_root))
                        items.append(rel_path)
                except ValueError:
                    continue
            return sorted(items)
        
        return []
    except Exception:
        return []


def _get_file_path_with_completion(prompt_text: str, default: str = None) -> str:
    """Get file path with tab completion support"""
    try:
        import readline
        
        readline.set_completer(_file_path_completer)
        readline.parse_and_bind("tab: complete")
        
        if default:
            console.print(f"[bold]{prompt_text}[/bold] [{default}]: ", end="")
        else:
            console.print(f"[bold]{prompt_text}[/bold]: ", end="")
        
        file_path = input()
        
        # Use default if empty input
        if not file_path and default:
            file_path = default
        
        readline.set_completer(None)
        
        return file_path
    except ImportError:
        console.print("[dim]Tip: Type 'ex' and press Tab for examples/ directory[/dim]")
        if default:
            return Prompt.ask(f"[bold]{prompt_text}[/bold]", default=default)
        else:
            return Prompt.ask(f"[bold]{prompt_text}[/bold]")


@app.command()
def plan_summary(
    image_path: str = typer.Argument(..., help="Path to the plan image file"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Skip cache and force fresh analysis"),
    model: str = typer.Option("claude-3-5-sonnet", "--model", help="AI model to use (gpt-4o, claude-3-5-sonnet)")
):
    """Extract plan summary from an image"""

    if not os.path.isabs(image_path):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_path = os.path.join(project_root, image_path)
    
    if not os.path.exists(image_path):
        console.print(f"[red]File not found: {image_path}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[green]Processing plan image: {image_path}[/green]")
    
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        console.print("[yellow]Analyzing image with AI...[/yellow]")
        
        summary = get_image_summary(image_data, use_cache=not no_cache, model=model)
        
        console.print("\n[bold]Plan Summary:[/bold]")
        console.print(Panel(
            summary,
            title="AI-Generated Plan Summary"
        ))
        
    except Exception as e:
        console.print(f"[red]Error processing image: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def door_dimensions(
    image_path: str = typer.Argument(..., help="Path to the door image file")
):
    """Extract door dimensions from an image"""
    if not os.path.isabs(image_path):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_path = os.path.join(project_root, image_path)
    
    if not os.path.exists(image_path):
        console.print(f"[red]File not found: {image_path}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[green]Processing door image: {image_path}[/green]")
    
    # Mock door dimensions extraction
    mock_dimensions = [
        {"door_id": "D001", "width": "36\"", "height": "80\"", "thickness": DOOR_THICKNESS, "type": "Single"},
        {"door_id": "D002", "width": "32\"", "height": "80\"", "thickness": DOOR_THICKNESS, "type": "Single"},
        {"door_id": "D003", "width": "60\"", "height": "80\"", "thickness": DOOR_THICKNESS, "type": "Double"},
        {"door_id": "D004", "width": "72\"", "height": "80\"", "thickness": DOOR_THICKNESS, "type": "Sliding"}
    ]
    
    console.print("\n[bold]Door Dimensions:[/bold]")
    for door in mock_dimensions:
        console.print(f"Door {door['door_id']}: {door['width']} x {door['height']} x {door['thickness']} ({door['type']})")


@app.command()
def door_cost(
    image_path: str = typer.Argument(..., help="Path to the plan image file"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Skip cache and force fresh analysis"),
    model: str = typer.Option("claude-3-5-sonnet", "--model", help="AI model to use (gpt-4o, claude-3-5-sonnet)")
):
    """Analyze plan image and calculate door material costs"""
    
    if not os.path.isabs(image_path):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_path = os.path.join(project_root, image_path)
    
    if not os.path.exists(image_path):
        console.print(f"[red]File not found: {image_path}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[green]Processing plan image: {image_path}[/green]")
    
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        console.print("[yellow]Analyzing image with AI...[/yellow]")
        
        # Get image analysis
        analysis_result = get_image_summary(image_data, use_cache=not no_cache, model=model)
        
        console.print("\n[bold]Image Analysis:[/bold]")
        console.print(Panel(
            analysis_result,
            title="AI-Generated Plan Analysis"
        ))
        
        # Calculate costs
        console.print("\n[yellow]Calculating material costs...[/yellow]")
        cost_result = calculate_cost_from_image_analysis(analysis_result)
        
        if "error" in cost_result:
            console.print(f"[red]Cost calculation error: {cost_result['error']}[/red]")
            return
        
        # Display cost summary
        plan_summary = cost_result.get('plan_summary', {})
        total_cost = plan_summary.get('total_cost', 0)
        total_doors = plan_summary.get('total_doors', 0)
        
        console.print(f"\n[bold green]Cost Summary:[/bold green]")
        console.print(f"Total Doors: {total_doors}")
        console.print(f"Total Cost: ${total_cost:.2f}")
        
        # Display individual door costs
        door_costs = cost_result.get('door_costs', [])
        if door_costs:
            console.print(f"\n[bold]Door Costs:[/bold]")
            for i, door_cost in enumerate(door_costs):
                if 'error' in door_cost:
                    console.print(f"[red]Door {i+1}: Error - {door_cost['error']}[/red]")
                else:
                    specs = door_cost.get('door_specs', {})
                    breakdown = door_cost.get('cost_breakdown', {})
                    total = door_cost.get('total_cost', 0)
                    
                    # Create table for each door
                    table = Table(title=f"Door {i+1}")
                    table.add_column("Property", style="cyan", no_wrap=True)
                    table.add_column("Value", style="magenta")
                    
                    table.add_row("Dimensions", f"{specs.get('width_cm', 0):.1f}cm x {specs.get('height_cm', 0):.1f}cm")
                    table.add_row("Profile", specs.get('profile', 'Unknown'))
                    table.add_row("Perimeter", f"{door_cost.get('perimeter_cm', 0):.1f}cm")
                    table.add_row("Bar Units", f"{breakdown.get('aluminium_bars_needed', 0):.1f}")
                    table.add_row("Bar Cost", f"${breakdown.get('aluminium_bars_cost', 0):.2f}")
                    table.add_row("Total Cost", f"${total:.2f}", style="bold green")
                    
                    console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error processing image: {e}[/red]")
        return


@app.command()
def door_components(
    image_path: str = typer.Argument(..., help="Path to the door image file"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Skip cache and force fresh analysis"),
    model: str = typer.Option("claude-3-5-sonnet", "--model", help="AI model to use (gpt-4o, claude-3-5-sonnet)")
):
    """Extract door components from an image"""
    # Resolve relative paths from project root
    if not os.path.isabs(image_path):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_path = os.path.join(project_root, image_path)
    
    if not os.path.exists(image_path):
        console.print(f"[red]File not found: {image_path}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[green]Processing door image: {image_path}[/green]")
    
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        console.print("[yellow]Analyzing image with AI...[/yellow]")
        
        # Get image analysis with door components
        analysis_result = get_image_summary(image_data, use_cache=not no_cache, model=model)
        
        console.print("\n[bold]Door Components Analysis:[/bold]")
        console.print(Panel(
            analysis_result,
            title="AI-Generated Door Components"
        ))
        
        # Try to parse and display structured components
        try:
            import json
            components_data = json.loads(analysis_result)
            
            if "doors" in components_data and components_data["doors"]:
                console.print(f"\n[bold green]Found {len(components_data['doors'])} door(s):[/bold green]")
                
                for i, door in enumerate(components_data["doors"]):
                    console.print(f"\n[bold]Door {i+1}:[/bold]")
                    
                    # Basic door info
                    door_table = Table(title=f"Door {i+1} Specifications")
                    door_table.add_column("Property", style="cyan", no_wrap=True)
                    door_table.add_column("Value", style="magenta")
                    
                    door_table.add_row("Type", door.get("type", "Unknown"))
                    door_table.add_row("Width", door.get("width", "Unknown"))
                    door_table.add_row("Height", door.get("height", "Unknown"))
                    door_table.add_row("Frame", door.get("frame", "Unknown"))
                    door_table.add_row("Preframe", door.get("preframe", "Unknown"))
                    door_table.add_row("Finish", door.get("finish", "Unknown"))
                    
                    console.print(door_table)
                    
                    # Panel details
                    if "panel" in door and door["panel"]:
                        panel = door["panel"]
                        console.print(f"\n[bold]Panel Details:[/bold]")
                        console.print(f"  Profile: {panel.get('profile', 'Unknown')}")
                        console.print(f"  Details: {panel.get('details', 'Unknown')}")
                    
                    # Accessories
                    if "accesories" in door and door["accesories"]:
                        console.print(f"\n[bold]Accessories:[/bold]")
                        for acc in door["accesories"]:
                            console.print(f"  • {acc.get('type', 'Unknown')}: {acc.get('item', 'Unknown')} (Qty: {acc.get('quantity', 'Unknown')})")
                    
            else:
                console.print("[yellow]No doors found in the analysis[/yellow]")
                
        except json.JSONDecodeError:
            console.print("[yellow]Could not parse structured components data[/yellow]")
            console.print("[dim]Raw analysis result displayed above[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error processing image: {e}[/red]")
        raise typer.Exit(1)

def _process_image_file(prompt_text: str, function, ask_cache: bool = False, ask_model: bool = False, default_path: str = None):
    """Process an image file with the given function"""
    image_path = _get_file_path_with_completion(prompt_text, default_path)
    if image_path:
        # If it's a relative path, resolve it from the project root (parent of cli/)
        if not os.path.isabs(image_path):
            # Get the project root (parent directory of cli/)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            image_path = os.path.join(project_root, image_path)
        
        if os.path.exists(image_path):
            no_cache = False
            if ask_cache:
                no_cache = not Prompt.ask("Use cache for faster processing?", choices=["y", "n"], default="y") == "y"
            
            model = "claude-3-5-sonnet"
            if ask_model:
                model = Prompt.ask("Select AI model", choices=["gpt-4o", "claude-3-5-sonnet"], default="claude-3-5-sonnet")
            
            try:
                if ask_model and ask_cache:
                    function(image_path, no_cache=no_cache, model=model)
                elif ask_cache:
                    function(image_path, no_cache=no_cache)
                else:
                    function(image_path)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        else:
            console.print(INVALID_PATH_MSG)
    else:
        console.print(INVALID_PATH_MSG)


def _handle_menu_choice(choice: str):
    """Handle menu choice and execute corresponding function"""
    if choice == "1":
        _process_image_file("Enter image file path for AI analysis", plan_summary, ask_cache=True, ask_model=True, default_path="examples/doors.png")
    elif choice == "2":
        _process_image_file("Enter door image file path", door_dimensions, ask_cache=False, ask_model=False, default_path="examples/doors.png")
    elif choice == "3":
        _process_image_file("Enter door image file path", door_components, ask_cache=True, ask_model=True, default_path="examples/doors.png")
    elif choice == "4":
        _process_image_file("Enter plan image file path for cost analysis", door_cost, ask_cache=True, ask_model=True, default_path="examples/doors.png")
    elif choice == "5":
        _process_image_file("Enter plan image file path for CSV export", export_csv_interactive, ask_cache=True, ask_model=True, default_path="examples/doors.png")
    elif choice == "6":
        catalog_shell()
    elif choice == "7":
        console.print("[green]Goodbye![/green]")
        return False
    
    return True


def export_csv_interactive(image_path: str, no_cache: bool = False, model: str = "claude-3-5-sonnet"):
    """Interactive CSV export function"""
    try:
        console.print(f"[green]Processing plan image: {image_path}[/green]")
        
        # Get image analysis
        console.print("Analyzing image with AI...")
        analysis_result = get_image_summary(image_path, use_cache=not no_cache, model=model)
        
        if not analysis_result:
            console.print("[red]Failed to analyze image[/red]")
            return
        
        # Calculate cost and export to CSV
        console.print("Calculating costs and generating CSV...")
        csv_path = calculate_and_export_cost_csv(analysis_result)
        
        console.print(f"[green]CSV exported successfully: {csv_path}[/green]")
        
        # Show preview of the CSV
        console.print("\n[bold]CSV Preview:[/bold]")
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:10]):  # Show first 10 lines
                    console.print(f"[dim]{i+1:2d}:[/dim] {line.strip()}")
                if len(lines) > 10:
                    console.print(f"[dim]... and {len(lines) - 10} more lines[/dim]")
        except Exception as e:
            console.print(f"[yellow]Could not preview CSV: {e}[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error processing image: {e}[/red]")
        return


@app.command()
def export_csv(
    image_path: str = typer.Argument(..., help="Path to the plan image file"),
    output_path: str = typer.Option(None, "--output", "-o", help="Output CSV file path (optional)")
):
    """Export door cost breakdown to CSV file"""
    # Resolve relative paths from project root
    if not os.path.isabs(image_path):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_path = os.path.join(project_root, image_path)
    
    if not os.path.exists(image_path):
        console.print(f"[red]File not found: {image_path}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[green]Processing plan image: {image_path}[/green]")
    
    try:
        # Get image analysis
        console.print("Analyzing image with AI...")
        analysis_result = get_image_summary(image_path)
        
        if not analysis_result:
            console.print("[red]Failed to analyze image[/red]")
            raise typer.Exit(1)
        
        # Calculate cost and export to CSV
        console.print("Calculating costs and generating CSV...")
        csv_path = calculate_and_export_cost_csv(analysis_result, output_path)
        
        console.print(f"[green]CSV exported successfully: {csv_path}[/green]")
        
        # Show preview of the CSV
        console.print("\n[bold]CSV Preview:[/bold]")
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:10]):  # Show first 10 lines
                    console.print(f"[dim]{i+1:2d}:[/dim] {line.strip()}")
                if len(lines) > 10:
                    console.print(f"[dim]... and {len(lines) - 10} more lines[/dim]")
        except Exception as e:
            console.print(f"[yellow]Could not preview CSV: {e}[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error processing image: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def catalog_shell():
    """Launch interactive catalog shell for filtering products"""
    console.print(Panel.fit(
        "[bold]Eigen3-SF Catalog Shell[/bold]\n"
        "Interactive shell for filtering and exploring the product catalog.\n"
        "[dim]Type 'help' for available commands, 'exit' to quit[/dim]",
        title="Welcome"
    ))
    
    # Initialize catalog
    cat = catalog()
    
    # Store current filter state
    current_filter = cat.all()
    
    while True:
        try:
            # Show current filter state
            count = current_filter.count()
            console.print(f"\n[bold blue]Current filter: {count} products[/bold blue]")
            
            # Get user input
            command = Prompt.ask("catalog>").strip()
            
            if not command:
                continue
                
            if command.lower() in ['exit', 'quit', 'q']:
                console.print("[green]Goodbye![/green]")
                break
                
            if command.lower() == 'help':
                _show_catalog_help()
                continue
                
            if command.lower() == 'reset':
                current_filter = cat.all()
                console.print("[green]Filter reset to all products[/green]")
                continue
                
            if command.lower() == 'show':
                _show_filtered_products(current_filter)
                continue
                
            if command.lower() == 'count':
                console.print(f"[bold]Total products: {current_filter.count()}[/bold]")
                continue
                
            # Try to execute the command
            try:
                # Evaluate the command in a safe context
                result = _execute_catalog_command(current_filter, command)
                if result is not None:
                    # Only update current_filter if result is a ProductFilter object
                    if hasattr(result, 'count') and callable(result.count):
                        current_filter = result
                        console.print(f"[green]Command executed. {current_filter.count()} products found.[/green]")
                    else:
                        # Result is a value (like count), just display it
                        console.print(f"[green]Result: {result}[/green]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                console.print("[dim]Type 'help' for available commands[/dim]")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit[/yellow]")
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")


def _show_catalog_help():
    """Show help for catalog shell commands"""
    help_text = """
[bold]Available Commands:[/bold]

[bold]Filtering:[/bold]
  .windows()                    - Filter for window-related products
  .doors()                      - Filter for door-related products
  .accessories()                - Filter for accessory products
  .profiles()                   - Filter for profile products
  .gala()                       - Filter for GALA system products
  .probba()                     - Filter for PROBBA system products
  .metta()                      - Filter for METTA system products
  .suprema()                    - Filter for SUPREMA system products
  .anodizado()                  - Filter for anodized finish products
  .pintado()                    - Filter for painted finish products
  .anolok()                     - Filter for Anolok finish products
  .color('color_name')          - Filter by specific color
  .price_range(min=1000, max=5000) - Filter by price range
  .search('search_term')        - Search for products containing term

[bold]Actions:[/bold]
  .get()                        - Get filtered products
  .count()                      - Get count of filtered products
  .first()                      - Get first product
  .last()                       - Get last product
  .reset()                      - Reset to all products

[bold]Shell Commands:[/bold]
  show                         - Display current filtered products
  count                        - Show count of current filter
  reset                        - Reset filter to all products
  help                         - Show this help
  exit/quit/q                  - Exit the shell

[bold]Examples:[/bold]
  .windows().accessories().gala().get()
  .doors().profiles().pintado().color('blanco').count()
  .all().search('manija').price_range(max=1000).show()
  .profiles().gala().anodizado().first()
"""
    console.print(help_text)


def _execute_catalog_command(current_filter, command):
    """Execute a catalog command safely"""
    # Handle shell commands first
    if command.strip() == 'show':
        return current_filter.show()
    elif command.strip() == 'count':
        return current_filter.count()
    elif command.strip() == 'reset':
        return current_filter.reset()
    elif command.strip() in ['help', 'exit', 'quit', 'q']:
        return None
    
    # Handle method chaining commands that start with a dot
    if command.strip().startswith('.'):
        # Remove the leading dot and execute as a method chain
        method_chain = command.strip()[1:]  # Remove the leading dot
        
        # Add the current filter as 'cat' in the local namespace
        local_vars = {
            'cat': current_filter,
            'catalog': catalog(),
            'current_filter': current_filter
        }
        
        # Add common methods to the namespace
        local_vars.update({
            'windows': lambda: current_filter.windows(),
            'doors': lambda: current_filter.doors(),
            'accessories': lambda: current_filter.accessories(),
            'profiles': lambda: current_filter.profiles(),
            'gala': lambda: current_filter.gala(),
            'probba': lambda: current_filter.probba(),
            'metta': lambda: current_filter.metta(),
            'suprema': lambda: current_filter.suprema(),
            'anodizado': lambda: current_filter.anodizado(),
            'pintado': lambda: current_filter.pintado(),
            'anolok': lambda: current_filter.anolok(),
            'color': lambda color: current_filter.color(color),
            'price_range': lambda min_price=None, max_price=None: current_filter.price_range(min_price, max_price),
            'search': lambda term: current_filter.search(term),
            'get': lambda: current_filter.get(),
            'count': lambda: current_filter.count(),
            'first': lambda: current_filter.first(),
            'last': lambda: current_filter.last(),
            'reset': lambda: current_filter.reset(),
        })
        
        try:
            # Execute the method chain
            result = eval(method_chain, {"__builtins__": {}}, local_vars)
            return result
        except Exception as e:
            raise Exception(f"Command execution failed: {e}")
    
    # Handle other commands
    else:
        # Add the current filter as 'cat' in the local namespace
        local_vars = {
            'cat': current_filter,
            'catalog': catalog(),
            'current_filter': current_filter
        }
        
        # Add common methods to the namespace
        local_vars.update({
            'windows': lambda: current_filter.windows(),
            'doors': lambda: current_filter.doors(),
            'accessories': lambda: current_filter.accessories(),
            'profiles': lambda: current_filter.profiles(),
            'gala': lambda: current_filter.gala(),
            'probba': lambda: current_filter.probba(),
            'metta': lambda: current_filter.metta(),
            'suprema': lambda: current_filter.suprema(),
            'anodizado': lambda: current_filter.anodizado(),
            'pintado': lambda: current_filter.pintado(),
            'anolok': lambda: current_filter.anolok(),
            'color': lambda color: current_filter.color(color),
            'price_range': lambda min_price=None, max_price=None: current_filter.price_range(min_price, max_price),
            'search': lambda term: current_filter.search(term),
            'get': lambda: current_filter.get(),
            'count': lambda: current_filter.count(),
            'first': lambda: current_filter.first(),
            'last': lambda: current_filter.last(),
            'reset': lambda: current_filter.reset(),
        })
        
        try:
            # Execute the command
            result = eval(command, {"__builtins__": {}}, local_vars)
            return result
        except Exception as e:
            raise Exception(f"Command execution failed: {e}")


def _show_filtered_products(current_filter, limit=10):
    """Show filtered products in a table"""
    products = current_filter.get()
    
    if not products:
        console.print("[yellow]No products found[/yellow]")
        return
    
    # Create table
    table = Table(title=f"Filtered Products (showing first {min(limit, len(products))} of {len(products)})")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("SKU", style="magenta")
    table.add_column("Price", style="green")
    table.add_column("Category", style="yellow")
    table.add_column("System", style="blue")
    
    for product in products[:limit]:
        name = product.get('name', 'Unknown')[:50] + "..." if len(product.get('name', '')) > 50 else product.get('name', 'Unknown')
        sku = product.get('sku', 'N/A')
        price = f"${product.get('price', 0):.2f}" if product.get('price') else 'N/A'
        category = product.get('main_category', 'Unknown')
        system = product.get('system', 'N/A')
        
        table.add_row(name, sku, price, category, system)
    
    console.print(table)
    
    if len(products) > limit:
        console.print(f"[dim]... and {len(products) - limit} more products[/dim]")


@app.command()
def interactive():
    """Launch interactive mode with menu"""
    console.print(Panel.fit(
        "[bold]Eigen3-SF Analysis Tools[/bold]\n"
        "Interactive mode for door analysis and plan extraction.\n"
        "[dim]Tip: Use Tab key for file path autocomplete[/dim]",
        title="Welcome"
    ))
    
    while True:
        console.print("\n[bold]Menu:[/bold]")
        console.print("1. Summary")
        console.print("2. Dimensions")
        console.print("3. Components")
        console.print("4. Materials")
        console.print("5. Export CSV")
        console.print("6. Catalog Shell")
        console.print("7. Exit")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6", "7"])
        
        if not _handle_menu_choice(choice):
            break

if __name__ == "__main__":
    import sys
    # If no arguments provided, run interactive mode
    if len(sys.argv) == 1:
        interactive()
    else:
        app()