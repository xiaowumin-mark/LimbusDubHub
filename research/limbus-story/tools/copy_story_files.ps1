param(
    [string]$GameRoot = "E:\Program Files (x86)\Steam\steamapps\common\Limbus Company"
)

$ErrorActionPreference = "Stop"

$AnalysisRoot = Split-Path -Parent $PSScriptRoot
$LocalizeRoot = Join-Path $GameRoot "LimbusCompany_Data\Assets\Resources_moved\Localize"
$AudioRoot = Join-Path $GameRoot "LimbusCompany_Data\StreamingAssets\Assets\Sound\FMODBuilds\Desktop"
$CopyRoot = Join-Path $AnalysisRoot "source-copy\Localize"
$AudioIndexRoot = Join-Path $AnalysisRoot "audio-index"
$SteamAppsRoot = Split-Path -Parent (Split-Path -Parent $GameRoot)
$AppManifest = Join-Path $SteamAppsRoot "appmanifest_1973530.acf"
$BuildId = $null

if (-not (Test-Path -LiteralPath $LocalizeRoot)) {
    throw "Localize root not found: $LocalizeRoot"
}
if (-not (Test-Path -LiteralPath $AudioRoot)) {
    throw "FMOD bank root not found: $AudioRoot"
}
if (Test-Path -LiteralPath $AppManifest) {
    $manifestText = Get-Content -Raw -LiteralPath $AppManifest
    if ($manifestText -match '"buildid"\s+"([^"]+)"') {
        $BuildId = $Matches[1]
    }
}

New-Item -ItemType Directory -Force -Path $CopyRoot, $AudioIndexRoot | Out-Null

foreach ($lang in "kr", "en", "jp") {
    $srcStory = Join-Path $LocalizeRoot "$lang\StoryData"
    $dstStory = Join-Path $CopyRoot "$lang\StoryData"
    New-Item -ItemType Directory -Force -Path $dstStory | Out-Null
    Get-ChildItem -LiteralPath $srcStory -File -Filter "*.json" |
        ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $dstStory -Force }

    $srcLang = Join-Path $LocalizeRoot $lang
    $dstMeta = Join-Path $CopyRoot "$lang\root-story-metadata"
    New-Item -ItemType Directory -Force -Path $dstMeta | Out-Null
    Get-ChildItem -LiteralPath $srcLang -File |
        Where-Object {
            $_.Name -match "^(KR|EN|JP)_(Story|Stage|StageNode|StageChapter|StoryTheater|StoryDungeon|StoryUI|StoryText)" -or
            $_.Name -match "Story|Stage"
        } |
        ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $dstMeta -Force }
}

New-Item -ItemType Directory -Force -Path (Join-Path $CopyRoot "etc") | Out-Null
Copy-Item -LiteralPath (Join-Path $LocalizeRoot "etc\VoiceTable.json") -Destination (Join-Path $CopyRoot "etc\VoiceTable.json") -Force
Copy-Item -LiteralPath (Join-Path $LocalizeRoot "RemoteLocalizeFileList.json") -Destination (Join-Path $CopyRoot "RemoteLocalizeFileList.json") -Force

$sourceInfo = [ordered]@{
    copiedAt = (Get-Date).ToString("s")
    gameRoot = $GameRoot
    localizeRoot = $LocalizeRoot
    audioRoot = $AudioRoot
    steamAppId = "1973530"
    steamBuildId = $BuildId
    note = "Story files were copied before JSON structure analysis. Do not edit files under the game install directory."
}
$sourceInfo | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $AnalysisRoot "source-info.json") -Encoding UTF8

Get-ChildItem -LiteralPath $AudioRoot -File |
    Select-Object Name,Length,LastWriteTime,
        @{Name = "BankId"; Expression = { $_.Name -replace "\.assets\.bank$", "" -replace "\.bank$", "" }},
        @{Name = "Kind"; Expression = { if ($_.Name -like "*.assets.bank") { "sample-data" } elseif ($_.Name -like "*.bank") { "metadata-events" } else { "other" } }} |
    Sort-Object BankId,Kind,Name |
    Export-Csv -LiteralPath (Join-Path $AudioIndexRoot "fmod_desktop_banks.csv") -NoTypeInformation -Encoding UTF8

Get-ChildItem -LiteralPath $CopyRoot -Recurse -File |
    Select-Object FullName,Length,LastWriteTime |
    Sort-Object FullName |
    Export-Csv -LiteralPath (Join-Path $AnalysisRoot "copied-files-manifest.csv") -NoTypeInformation -Encoding UTF8

$counts = [ordered]@{
    copiedFiles = (Get-ChildItem -LiteralPath $CopyRoot -Recurse -File).Count
    copiedBytes = [int64]((Get-ChildItem -LiteralPath $CopyRoot -Recurse -File | Measure-Object Length -Sum).Sum)
    krStoryData = (Get-ChildItem -LiteralPath (Join-Path $CopyRoot "kr\StoryData") -File).Count
    enStoryData = (Get-ChildItem -LiteralPath (Join-Path $CopyRoot "en\StoryData") -File).Count
    jpStoryData = (Get-ChildItem -LiteralPath (Join-Path $CopyRoot "jp\StoryData") -File).Count
    audioIndexRows = (Import-Csv -LiteralPath (Join-Path $AudioIndexRoot "fmod_desktop_banks.csv")).Count
}
$counts | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $AnalysisRoot "copy-summary.json") -Encoding UTF8
$counts | Format-List
