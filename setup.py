#!/usr/bin/env python3
"""
Setup script for Ethereum Transaction Tracker
Helps users install dependencies and configure the environment.
"""

import os
import sys
import subprocess
import shutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 7):
        logger.error("❌ Python 3.7 or higher is required")
        logger.error(f"Current version: {sys.version}")
        return False
    logger.info(f"✅ Python version: {sys.version}")
    return True

def install_dependencies():
    """Install required Python packages."""
    logger.info("\nInstalling dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Set up environment configuration."""
    logger.info("\nSetting up environment...")
    
    # Check if .env exists
    if os.path.exists('.env'):
        logger.info("✅ .env file already exists")
        return True
    
    # Copy config.env to .env if it exists
    if os.path.exists('config.env'):
        shutil.copy('config.env', '.env')
        logger.info("✅ Created .env file from config.env")
        logger.info("📝 Please edit .env and add your API keys")
        return True
    else:
        logger.warning("⚠️  config.env not found, creating basic .env file")
        with open('.env', 'w') as f:
            f.write("# Ethereum Transaction Tracker Configuration\n")
            f.write("# Add your API keys here\n\n")
            f.write("ETHERSCAN_API_KEY=your_etherscan_api_key_here\n")
            f.write("ALCHEMY_API_KEY=your_alchemy_api_key_here\n")
        logger.info("✅ Created basic .env file")
        logger.info("📝 Please edit .env and add your API keys")
        return True

def test_imports():
    """Test if all required modules can be imported."""
    logger.info("\nTesting imports...")
    try:
        import requests
        import pandas
        import web3
        from dotenv import load_dotenv
        logger.info("✅ All required modules imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False

def main():
    """Main setup function."""
    logger.info("Ethereum Transaction Tracker Setup")
    logger.info("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Test imports
    if not test_imports():
        return False
    
    # Setup environment
    if not setup_environment():
        return False
    
    logger.info("\n" + "=" * 40)
    logger.info("✅ Setup completed successfully!")
    logger.info("\nNext steps:")
    logger.info("1. Edit .env file and add your API keys")
    logger.info("2. Run: python ethereum_transaction_tracker.py <wallet_address>")
    logger.info("3. Example: python ethereum_transaction_tracker.py 0xa39b189482f984388a34460636fea9eb181ad1a6")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
