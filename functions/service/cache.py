import hashlib
import pickle
from pathlib import Path
from typing import Optional
import shutil

# Cache configuration
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# PDF output directory
PDF_DIR = Path("pdfs")
PDF_DIR.mkdir(exist_ok=True)


def get_cache_key(prompt: str, image_data: bytes = None, model: str = "gpt-4o", prefix: str = "general") -> str:
    """Generate a cache key based on prompt, image, model, and operation type."""
    content = f"{model}:{prompt}"
    if image_data:
        # Include image hash for image-based prompts
        image_hash = hashlib.md5(image_data).hexdigest()
        content += f":img_{image_hash}"
    
    hash_key = hashlib.sha256(content.encode()).hexdigest()
    return f"{prefix}_{hash_key}"


def get_cached_response(cache_key: str) -> Optional[str]:
    """Retrieve cached response if it exists."""
    cache_file = CACHE_DIR / f"{cache_key}.pkl"
    if cache_file.exists():
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                print(f"Cache hit: Using cached response ({len(cached_data)} chars)")
                return cached_data
        except Exception as e:
            print(f"Cache read error: {e}")
            # Delete corrupted cache file
            cache_file.unlink(missing_ok=True)
    return None


def save_cached_response(cache_key: str, response: str) -> None:
    """Save response to cache."""
    try:
        cache_file = CACHE_DIR / f"{cache_key}.pkl"
        with open(cache_file, 'wb') as f:
            pickle.dump(response, f)
        print(f"Response cached ({len(response)} chars)")
    except Exception as e:
        print(f"Cache write error: {e}")


def get_cached_pdf(cache_key: str) -> Optional[Path]:
    """Check if PDF is cached and return path."""
    pdf_file = PDF_DIR / f"{cache_key}.pdf"
    if pdf_file.exists():
        print(f"PDF cache hit: Using cached PDF ({pdf_file})")
        return pdf_file
    return None


def save_cached_pdf(cache_key: str, pdf_path: Path) -> None:
    """Save PDF to cache with cache key name."""
    try:
        cached_pdf_path = PDF_DIR / f"{cache_key}.pdf"
        if pdf_path != cached_pdf_path:
            shutil.copy2(pdf_path, cached_pdf_path)
        print(f"PDF cached: {cached_pdf_path}")
    except Exception as e:
        print(f"PDF cache error: {e}")
