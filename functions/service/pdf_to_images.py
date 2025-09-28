#!/usr/bin/env python3
"""
PDF to Images converter - converts PDF pages to individual image files.
Supports multiple output formats and DPI settings.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import tempfile
import subprocess

def check_dependencies() -> Tuple[bool, List[str]]:
    """
    Check if required dependencies are available.
    
    Returns:
        Tuple of (all_available, missing_dependencies)
    """
    missing = []
    
    # Check for pdftoppm (from poppler-utils)
    try:
        subprocess.run(['pdftoppm', '-h'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append('pdftoppm (install poppler-utils)')
    
    return len(missing) == 0, missing

def pdf_to_images(pdf_path: str, output_dir: str = None, 
                 format: str = 'png', dpi: int = 300, 
                 prefix: str = 'page') -> List[Path]:
    """
    Convert PDF pages to individual image files.
    
    Args:
        pdf_path: Path to input PDF file
        output_dir: Directory to save images (default: same as PDF)
        format: Output format ('png', 'jpeg', 'tiff', 'ppm')
        dpi: Resolution in DPI (default: 300)
        prefix: Prefix for output filenames
        
    Returns:
        List of paths to generated image files
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        RuntimeError: If conversion fails
    """
    # Validate inputs
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Check dependencies
    deps_ok, missing = check_dependencies()
    if not deps_ok:
        raise RuntimeError(f"Missing dependencies: {', '.join(missing)}")
    
    # Set output directory
    if output_dir is None:
        output_dir = pdf_file.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Validate format
    valid_formats = ['png', 'jpeg', 'tiff', 'ppm']
    if format not in valid_formats:
        raise ValueError(f"Invalid format: {format}. Must be one of {valid_formats}")
    
    print(f"Converting PDF to images...")
    print(f"Input: {pdf_file}")
    print(f"Output directory: {output_dir}")
    print(f"Format: {format}, DPI: {dpi}")
    
    # Build pdftoppm command
    output_prefix = output_dir / prefix
    
    cmd = [
        'pdftoppm',
        '-r', str(dpi),  # Resolution
        f'-{format}',    # Output format
        str(pdf_file),   # Input PDF
        str(output_prefix)  # Output prefix
    ]
    
    try:
        # Run conversion
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("PDF conversion completed successfully")
        
        # Find generated files
        pattern = f"{prefix}-*.{format}"
        image_files = list(output_dir.glob(pattern))
        
        # Sort by page number
        image_files.sort(key=lambda x: int(x.stem.split('-')[-1]))
        
        print(f"Generated {len(image_files)} image files:")
        for img_file in image_files:
            print(f"  - {img_file}")
        
        return image_files
        
    except subprocess.CalledProcessError as e:
        error_msg = f"PDF conversion failed: {e.stderr}"
        print(error_msg)
        raise RuntimeError(error_msg)

def get_pdf_page_count(pdf_path: str) -> int:
    """
    Get the number of pages in a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Number of pages in the PDF
    """
    try:
        # Use pdfinfo to get page count
        result = subprocess.run([
            'pdfinfo', str(pdf_path)
        ], capture_output=True, text=True, check=True)
        
        # Parse output for page count
        for line in result.stdout.split('\n'):
            if line.startswith('Pages:'):
                return int(line.split(':')[1].strip())
        
        # Fallback: try pdftoppm to count pages
        result = subprocess.run([
            'pdftoppm', '-f', '1', '-l', '1', str(pdf_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            # If single page works, try to get actual count
            return 1  # Minimum fallback
        
        return 0
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: Could not determine PDF page count")
        return 0

def batch_convert_pdfs(pdf_directory: str, output_directory: str = None,
                      format: str = 'png', dpi: int = 300) -> dict:
    """
    Convert multiple PDF files to images.
    
    Args:
        pdf_directory: Directory containing PDF files
        output_directory: Directory to save all images
        format: Output image format
        dpi: Resolution in DPI
        
    Returns:
        Dictionary mapping PDF filenames to list of generated image paths
    """
    pdf_dir = Path(pdf_directory)
    if not pdf_dir.exists():
        raise FileNotFoundError(f"Directory not found: {pdf_directory}")
    
    # Find all PDF files
    pdf_files = list(pdf_dir.glob('*.pdf'))
    if not pdf_files:
        print("No PDF files found in directory")
        return {}
    
    print(f"Found {len(pdf_files)} PDF files to convert")
    
    results = {}
    
    for pdf_file in pdf_files:
        try:
            # Create subdirectory for each PDF
            if output_directory:
                pdf_output_dir = Path(output_directory) / pdf_file.stem
            else:
                pdf_output_dir = pdf_file.parent / f"{pdf_file.stem}_images"
            
            pdf_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert PDF
            image_files = pdf_to_images(
                str(pdf_file), 
                str(pdf_output_dir), 
                format=format, 
                dpi=dpi,
                prefix=pdf_file.stem
            )
            
            results[pdf_file.name] = image_files
            print(f"✓ Converted {pdf_file.name}: {len(image_files)} pages")
            
        except Exception as e:
            print(f"✗ Failed to convert {pdf_file.name}: {e}")
            results[pdf_file.name] = []
    
    return results

def main():
    """Command line interface for PDF to images conversion."""
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_images.py <pdf_file> [output_dir] [format] [dpi]")
        print("       python pdf_to_images.py --batch <pdf_directory> [output_dir] [format] [dpi]")
        print("")
        print("Formats: png, jpeg, tiff, ppm")
        print("Default DPI: 300")
        sys.exit(1)
    
    try:
        if sys.argv[1] == '--batch':
            # Batch mode
            pdf_directory = sys.argv[2] if len(sys.argv) > 2 else '.'
            output_directory = sys.argv[3] if len(sys.argv) > 3 else None
            format = sys.argv[4] if len(sys.argv) > 4 else 'png'
            dpi = int(sys.argv[5]) if len(sys.argv) > 5 else 300
            
            results = batch_convert_pdfs(pdf_directory, output_directory, format, dpi)
            
            print(f"\nBatch conversion completed:")
            print(f"Successfully converted: {sum(1 for files in results.values() if files)}")
            print(f"Failed conversions: {sum(1 for files in results.values() if not files)}")
            
        else:
            # Single file mode
            pdf_file = sys.argv[1]
            output_dir = sys.argv[2] if len(sys.argv) > 2 else None
            format = sys.argv[3] if len(sys.argv) > 3 else 'png'
            dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 300
            
            # Get page count first
            page_count = get_pdf_page_count(pdf_file)
            if page_count > 0:
                print(f"PDF has {page_count} pages")
            
            # Convert PDF
            image_files = pdf_to_images(pdf_file, output_dir, format, dpi)
            
            print(f"\nConversion completed successfully!")
            print(f"Generated {len(image_files)} image files")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
