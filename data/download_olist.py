import os
import zipfile
import subprocess
import sys

def download_olist_dataset():
    """
    Downloads the Brazilian E-Commerce Public Dataset by Olist from Kaggle.
    Requires kaggle library and a valid ~/.kaggle/kaggle.json authentication file.
    """
    data_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_name = "olistbr/brazilian-ecommerce"
    zip_path = os.path.join(data_dir, "brazilian-ecommerce.zip")

    print("Checking for kaggle library...")
    try:
        import kaggle
    except ImportError:
        print("Kaggle library not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "kaggle"])
        import kaggle

    print(f"Downloading dataset '{dataset_name}' to {data_dir}...")
    try:
        # Programmatic Kaggle API download
        kaggle.api.authenticate()
        kaggle.api.dataset_download_files(dataset_name, path=data_dir, unzip=False)
        print("Download complete.")

        print("Extracting files...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(data_dir)
        print("Extraction complete.")
        
        # Cleanup zip file
        os.remove(zip_path)
        print("Done! You are ready to run the ML pipeline with real data.")

    except Exception as e:
        print("\n[ERROR] Failed to download dataset.")
        print("Make sure you have a Kaggle account and have placed your 'kaggle.json' API key in:")
        print("  - Windows: C:\\Users\\<Username>\\.kaggle\\kaggle.json")
        print("  - Mac/Linux: ~/.kaggle/kaggle.json")
        print(f"\nDetails: {e}")

if __name__ == "__main__":
    download_olist_dataset()
