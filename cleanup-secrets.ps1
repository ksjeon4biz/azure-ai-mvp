# ========================================
# Git 히스토리에서 민감정보 완전 제거 스크립트
# - 실행 위치: 저장소 루트
# - 영향: 커밋 히스토리 재작성 + 강제 푸시
# ========================================

$ErrorActionPreference = "Stop"

# === 사용자 설정 ===
# 강제 푸시할 대상 브랜치 (보통 main)
$TargetBranch = "main"
# 새 브랜치로 푸시하고 싶으면 $UseNewBranch = $true 로 변경
$UseNewBranch = $false
$NewBranchName = "clean-main"

Write-Host "=== 0) 사전 점검 ==="
git --version
git status

# 안전장치: 작업 디렉토리 깨끗한지
$gitStatus = git status --porcelain
if ($gitStatus) {
  Write-Host "작업 디렉토리가 깨끗하지 않습니다. 변경사항을 커밋/스태시 후 다시 실행하세요." -ForegroundColor Yellow
  exit 1
}

Write-Host "=== 1) 현재 커밋에서 민감 파일 제거 & .gitignore 등록 ==="
# 민감 파일: settings.json (특정 경로 및 모든 위치)
$SensitivePaths = @(
  "backend/azure_function/log_uploader/settings.json"
)

foreach ($p in $SensitivePaths) {
  if (Test-Path $p) {
    git rm --cached $p -f
    Remove-Item -Force $p
  }
}


# .gitignore 업데이트
if (!(Test-Path ".gitignore")) { New-Item -ItemType File -Path ".gitignore" | Out-Null }
@"
.env
settings.json
local.settings.json
"@ | Add-Content ".gitignore"

git add .gitignore
git commit -m "chore: remove sensitive files and ignore .env/settings.json"

Write-Host "=== 2) git-filter-repo 설치 확인 ==="
if (-not (Get-Command git-filter-repo -ErrorAction SilentlyContinue)) {
    Write-Host "git-filter-repo 설치 중..."
    pip install git-filter-repo
}

Write-Host "=== 3) 히스토리에서 민감 '파일' 완전 삭제 ==="
# 동일/과거 경로 변화까지 포함하여 모든 settings.json 제거
# (원한다면 다른 경로도 --path/--path-glob 로 추가)
git filter-repo --force --invert-paths `
  --path backend/azure_function/log_uploader/settings.json `
  --path-glob "*settings.json"

Write-Host "=== 4) 히스토리에서 '문자열' 기반 비밀 치환 ==="
# JSON/ dotenv 스타일 모두 커버하는 정규식
$replaceText = @"
# JSON key-value: "KEY": "VALUE"  -> "KEY": "<REDACTED>"
("AZURE_OPENAI_API_KEY"\s*:\s*")[^"]+(") => $1<REDACTED>$2
("AZURE_SEARCH_KEY"\s*:\s*")[^"]+(")   => $1<REDACTED>$2
("APPLICATIONINSIGHTS_CONNECTION_STRING"\s*:\s*")[^"]+(") => $1<REDACTED>$2
("AZURE_STORAGE_CONNECTION"\s*:\s*")[^"]+(") => $1<REDACTED>$2
("LANGCHAIN_API_KEY"\s*:\s*")[^"]+(")  => $1<REDACTED>$2
("LANGSMITH_API_KEY"\s*:\s*")[^"]+(")  => $1<REDACTED>$2
("LANGFUSE_PUBLIC_KEY"\s*:\s*")[^"]+(")=> $1<REDACTED>$2
("LANGFUSE_SECRET_KEY"\s*:\s*")[^"]+(")=> $1<REDACTED>$2

# .env 스타일: KEY=VALUE -> KEY=<REDACTED>
(^AZURE_OPENAI_API_KEY\s*=\s*).*$ => ${1}<REDACTED>
(^AZURE_SEARCH_KEY\s*=\s*).*$    => ${1}<REDACTED>
(^APPLICATIONINSIGHTS_CONNECTION_STRING\s*=\s*).*$ => ${1}<REDACTED>
(^AZURE_STORAGE_CONNECTION\s*=\s*).*$ => ${1}<REDACTED>
(^LANGCHAIN_API_KEY\s*=\s*).*$    => ${1}<REDACTED>
(^LANGSMITH_API_KEY\s*=\s*).*$    => ${1}<REDACTED>
(^LANGFUSE_PUBLIC_KEY\s*=\s*).*$  => ${1}<REDACTED>
(^LANGFUSE_SECRET_KEY\s*=\s*).*$  => ${1}<REDACTED>

# Azure Storage 연결문자열 패턴 (안전망)
(DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=)[^;]+(;) => ${1}<REDACTED>${2}
"@

$replaceFile = "replace.txt"
$replaceText | Out-File -Encoding utf8 $replaceFile

git filter-repo --force --replace-text $replaceFile
Remove-Item -Force $replaceFile

Write-Host "=== 5) 원본 refs 완전 제거 + GC ==="
# filter-repo가 남길 수 있는 백업 refs 제거
git for-each-ref --format="%(refname)" refs/original/ | ForEach-Object { git update-ref -d $_ }
git for-each-ref --format="%(refname)" refs/replace/  | ForEach-Object { git update-ref -d $_ }
git reflog expire --expire=now --all
git gc --prune=now --aggressive

Write-Host "=== 6) 로컬 검사 (샘플) ==="
# 과거 전체 커밋에서 민감 키 조각 검색 (없어야 정상)
# 필요시 키 일부 문자열로 교체해서 검증하세요.
# 예) git grep -I -n -r "InstrumentationKey=" $(git rev-list --all)
# 예) git grep -I -n -r "AccountKey=" $(git rev-list --all)

Write-Host "=== 7) 푸시 ==="
if ($UseNewBranch) {
  git checkout -b $NewBranchName
  git push origin --force --set-upstream $NewBranchName
  Write-Host "새 브랜치 $NewBranchName 으로 강제 푸시 완료. GitHub에서 기본 브랜치를 $NewBranchName 으로 변경 후 기존 브랜치 삭제하세요."
} else {
  # 모든 브랜치/태그 강제 반영 & 불필요한 참조 제거
  git push origin --force --all --prune
  git push origin --force --tags --prune
  Write-Host "기존 브랜치/태그에 강제 푸시 완료."
}

Write-Host "`n✅ 완료! GitHub Secret Scanning 경고가 사라졌는지 확인하세요."
Write-Host "⚠️ 보안 권장: 노출된 키는 반드시 '회수/재발급(rotate)' 하세요."
