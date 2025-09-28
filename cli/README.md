# Eigen3-SF CLI

Modern command-line interface for Eigen3-SF analysis tools built with Typer and Rich.

## Features

- 📸 Image analysis and BOM extraction
- 📄 PDF to image conversion  
- 📝 LaTeX document generation
- 💾 Results saving and export
- 🎨 Beautiful terminal output with Rich
- ⚡ Fast and responsive with progress indicators

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

3. Run the CLI:
```bash
python main.py --help
```

## Usage

### Command Line Interface

The CLI provides several commands:

#### Analyze Image
```bash
python main.py analyze image.jpg --save
python main.py analyze image.jpg --output results/
```

#### Extract BOM Only
```bash
python main.py bom image.jpg --output bom_data.json
python main.py bom image.jpg --context "Door assembly drawing"
```

#### Convert PDF to Images
```bash
python main.py pdf document.pdf --output images/ --format png --dpi 300
```

#### Generate LaTeX Document
```bash
python main.py latex --image image.jpg --output report
python main.py latex --summary "Door analysis" --bom bom_data.json --output report
```

#### Interactive Mode
```bash
python main.py interactive
```

### Command Options

- `--help` - Show help for any command
- `--output, -o` - Specify output directory or file
- `--save, -s` - Save results to files
- `--context, -c` - Additional context for analysis
- `--format, -f` - Output format for PDF conversion
- `--dpi, -d` - DPI for PDF conversion

## Dependencies

- OpenAI API key for image analysis
- pdftoppm (from poppler-utils) for PDF conversion
- pdflatex for LaTeX compilation
- typer for CLI framework
- rich for beautiful terminal output
