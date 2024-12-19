#!/usr/bin/env python
import subprocess
import sys
import time
import os

def run_script(script_name, *args):
    """Run a Python script with arguments and handle its output"""
    print(f"\n{'='*80}")
    print(f"🚀 Executing {script_name}")
    print(f"{'='*80}\n")
    
    try:
        cmd = [sys.executable, script_name] + list(args)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Print output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                
        # Get the return code
        return_code = process.poll()
        
        if return_code == 0:
            print(f"\n✅ {script_name} completed successfully!")
            return True
        else:
            error = process.stderr.read()
            print(f"\n❌ {script_name} failed with error:")
            print(error)
            return False
            
    except Exception as e:
        print(f"\n❌ Error running {script_name}: {str(e)}")
        return False

def main(pdf_path):
    """
    Main pipeline to process PDF and create knowledge graph
    
    Args:
        pdf_path: Path to the PDF file to process
    """
    start_time = time.time()
    
    print("\n📚 Starting PDF Processing Pipeline")
    print(f"Input PDF: {pdf_path}")
    
    # Step 1: Extract Table of Contents
    print("\n📑 Step 1/4: Extracting Table of Contents")
    if not run_script("TOCExtractor.py", pdf_path):
        print("❌ Pipeline failed at TOC extraction step")
        return
    
    # Step 2: Extract Content
    print("\n📝 Step 2/4: Extracting Content")
    if not run_script("ContentExtractor.py", pdf_path):
        print("❌ Pipeline failed at content extraction step")
        return
    
    # Step 3: Create Structured Concept Graph
    print("\n🔄 Step 3/4: Creating Structured Concept Graph")
    if not run_script("StructuredConceptGraph.py"):
        print("❌ Pipeline failed at concept graph creation step")
        return
    
    # Step 4: Create Vector Index
    print("\n📊 Step 4/4: Creating Vector Index")
    if not run_script("vectorIndexCreation.py"):
        print("❌ Pipeline failed at vector index creation step")
        return
    
    # Calculate total execution time
    execution_time = time.time() - start_time
    minutes = int(execution_time // 60)
    seconds = int(execution_time % 60)
    
    print("\n✨ Pipeline completed successfully!")
    print(f"⏱️  Total execution time: {minutes} minutes and {seconds} seconds")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python data_pipeline.py <pdf_path>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found at {pdf_path}")
        sys.exit(1)
        
    main(pdf_path)
