import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional

# PDF output directory
PDF_DIR = Path("pdfs")
PDF_DIR.mkdir(exist_ok=True)


def compile_latex_to_pdf(latex_content: str, output_filename: str) -> Optional[Path]:
    """
    Compile LaTeX content to PDF using pdflatex.
    
    Args:
        latex_content: LaTeX document content
        output_filename: Name for the output PDF file
        
    Returns:
        Path to generated PDF or None if compilation failed
    """
    try:
        # Check if pdflatex is available
        try:
            subprocess.run(['pdflatex', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: pdflatex not found. Please install TeX Live or MiKTeX")
            return None
        
        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            tex_file = temp_path / "document.tex"
            
            # Write LaTeX content to file
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            # Compile LaTeX to PDF (run twice for proper references)
            print("Compiling LaTeX to PDF...")
            for i in range(2):
                result = subprocess.run([
                    'pdflatex', 
                    '-interaction=nonstopmode',
                    '-output-directory', str(temp_path),
                    str(tex_file)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"LaTeX compilation error (stderr): {result.stderr}")
                    print(f"LaTeX compilation error (stdout): {result.stdout}")
                    return None
            
            # Check if PDF was generated
            pdf_file = temp_path / "document.pdf"
            if not pdf_file.exists():
                print("Error: PDF file was not generated")
                print(f"Checked path: {pdf_file}")
                # List files in temp directory for debugging
                import os
                temp_files = os.listdir(temp_path)
                print(f"Files in temp directory: {temp_files}")
                return None
            
            # Move PDF to output directory
            output_path = PDF_DIR / f"{output_filename}.pdf"
            shutil.copy2(pdf_file, output_path)
            
            print(f"PDF generated successfully: {output_path}")
            return output_path
            
    except Exception as e:
        print(f"Error compiling LaTeX to PDF: {e}")
        return None
