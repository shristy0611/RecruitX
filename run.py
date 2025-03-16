import streamlit.cli as stcli
import sys
from pathlib import Path

if __name__ == "__main__":
    # Add the src directory to Python path
    src_path = Path(__file__).parent / "src"
    sys.path.append(str(src_path))
    
    # Run the Streamlit app
    sys.argv = ["streamlit", "run", "agents/streamlit_app.py"]
    sys.exit(stcli.main()) 