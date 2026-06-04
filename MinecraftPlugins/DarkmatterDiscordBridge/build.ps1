$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BuildDir = Join-Path $ProjectRoot "build"
$ClassesDir = Join-Path $BuildDir "classes"
$LibsDir = Join-Path $BuildDir "libs"
$DistDir = Join-Path $ProjectRoot "dist"
$PaperApiVersion = $env:PAPER_API_VERSION
if ([string]::IsNullOrWhiteSpace($PaperApiVersion)) {
    $PaperApiVersion = "26.1.2.build.69-stable"
}

$JavaHome = $env:JAVA_HOME
if ([string]::IsNullOrWhiteSpace($JavaHome)) {
    $AdoptiumJava = Get-ChildItem "C:\Program Files\Eclipse Adoptium" -Recurse -Filter javac.exe -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending |
        Select-Object -First 1
    if ($AdoptiumJava) {
        $JavaHome = Split-Path -Parent (Split-Path -Parent $AdoptiumJava.FullName)
    }
}

$Javac = if ($JavaHome) { Join-Path $JavaHome "bin\javac.exe" } else { "javac" }
$Jar = if ($JavaHome) { Join-Path $JavaHome "bin\jar.exe" } else { "jar" }

Remove-Item -LiteralPath $ClassesDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $ClassesDir, $LibsDir, $DistDir | Out-Null

function Get-MavenJar {
    param(
        [string] $GroupId,
        [string] $ArtifactId,
        [string] $Version
    )

    $GroupPath = $GroupId.Replace(".", "/")
    $FileName = "$ArtifactId-$Version.jar"
    $JarPath = Join-Path $LibsDir $FileName
    if (-not (Test-Path $JarPath)) {
        $Url = "https://repo.papermc.io/repository/maven-public/$GroupPath/$ArtifactId/$Version/$FileName"
        & curl.exe -L $Url -o $JarPath
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to download ${GroupId}:${ArtifactId}:${Version}"
        }
    }
}

$PaperApiJar = Join-Path $LibsDir "paper-api-$PaperApiVersion.jar"
if (-not (Test-Path $PaperApiJar)) {
    $Url = "https://repo.papermc.io/repository/maven-public/io/papermc/paper/paper-api/$PaperApiVersion/paper-api-$PaperApiVersion.jar"
    & curl.exe -L $Url -o $PaperApiJar
}

Get-MavenJar "net.kyori" "adventure-api" "4.26.1"
Get-MavenJar "net.kyori" "adventure-key" "4.26.1"
Get-MavenJar "net.kyori" "examination-api" "1.3.0"
Get-MavenJar "net.kyori" "examination-string" "1.3.0"
Get-MavenJar "org.jetbrains" "annotations" "26.0.2-1"
Get-MavenJar "org.jspecify" "jspecify" "1.0.0"
Get-MavenJar "org.checkerframework" "checker-qual" "3.49.2"
Get-MavenJar "com.google.guava" "guava" "33.5.0-jre"
Get-MavenJar "com.google.code.gson" "gson" "2.13.2"
Get-MavenJar "org.yaml" "snakeyaml" "2.2"
Get-MavenJar "org.joml" "joml" "1.10.8"
Get-MavenJar "it.unimi.dsi" "fastutil" "8.5.18"
Get-MavenJar "org.apache.logging.log4j" "log4j-api" "2.25.2"
Get-MavenJar "org.slf4j" "slf4j-api" "2.0.17"
Get-MavenJar "com.mojang" "brigadier" "1.3.10"
Get-MavenJar "net.md-5" "bungeecord-chat" "1.21-R0.2-deprecated+build.21"
Get-MavenJar "org.apache.maven" "maven-resolver-provider" "3.9.6"

$Sources = Get-ChildItem (Join-Path $ProjectRoot "src\main\java") -Recurse -Filter *.java | ForEach-Object { $_.FullName }
$Classpath = (Get-ChildItem $LibsDir -Filter *.jar | ForEach-Object { $_.FullName }) -join [IO.Path]::PathSeparator
& $Javac --release 25 -cp $Classpath -d $ClassesDir $Sources
if ($LASTEXITCODE -ne 0) {
    throw "javac failed with exit code $LASTEXITCODE"
}
Copy-Item (Join-Path $ProjectRoot "plugin.yml") $ClassesDir -Force
Copy-Item (Join-Path $ProjectRoot "config.yml") $ClassesDir -Force

$OutputJar = Join-Path $DistDir "DarkmatterDiscordBridge.jar"
Push-Location $ClassesDir
& $Jar cf $OutputJar .
if ($LASTEXITCODE -ne 0) {
    throw "jar failed with exit code $LASTEXITCODE"
}
Pop-Location

Write-Host "Built $OutputJar"
