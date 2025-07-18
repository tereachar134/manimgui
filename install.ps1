# install.ps1
$repo = "https://github.com/tereachar134/manimgui"
$tempDir = "$env:TEMP\manimgui"

Write-Host "Installing Manim GUI Editor (by Dimensional Algebra)" -ForegroundColor Cyan

# Download files
New-Item -ItemType Directory -Path $tempDir -Force
Invoke-WebRequest "$repo/raw/main/manimgui.py" -OutFile "$tempDir\manimgui.py"
Invoke-WebRequest "$repo/raw/main/requirements.txt" -OutFile "$tempDir\requirements.txt"

# Install Python dependencies
python -m pip install --upgrade pip
pip install -r "$tempDir\requirements.txt"

Write-Host "Installation complete! Run with: python $tempDir\manimgui.py" -ForegroundColor Green
