import sys
try:
    with open(r"c:\JOB AI\backend\server.log", "r", encoding="utf-16le") as f:
        lines = f.readlines()
        
    error_lines = []
    in_error = False
    for line in lines[-200:]: # check last 200 lines
        if "ERROR:" in line or "Exception in" in line or "Traceback" in line or in_error:
            in_error = True
            error_lines.append(line)
        if line.startswith("INFO:") and in_error:
            in_error = False
            
    if error_lines:
        print("".join(error_lines[-50:]))
    else:
        print("No Python Exception found in the last 200 lines.")
except Exception as e:
    print("Error:", e)
