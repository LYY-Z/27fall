$ErrorActionPreference = 'Stop'

$workspaceRoot = 'F:\27fall\申请材料'
$packageRoot = Join-Path $workspaceRoot '00_当前申请\02_学校提交包'
$outputRoot = Join-Path $workspaceRoot '00_当前申请\03_最终提交与推荐人确认包_2027Fall'

$programs = @(
    [pscustomobject]@{ Index = 1; Source = '01_PolyU_IRE'; Folder = '香港理工大学_智能机器人工程'; Cn = '香港理工大学 智能机器人工程理学硕士'; CnShort = '港理工_智能机器人工程'; EnTag = 'PolyU_MSc_Intelligent_Robotics_Engineering'; Pending = $false },
    [pscustomobject]@{ Index = 2; Source = '02_CUHKShenzhen_MAIR'; Folder = '香港中文大学深圳_人工智能与机器人'; Cn = '香港中文大学（深圳）人工智能与机器人理学硕士'; CnShort = '港中深_人工智能与机器人'; EnTag = 'CUHKSZ_MSc_AI_and_Robotics'; Pending = $false },
    [pscustomobject]@{ Index = 3; Source = '08_CUHKShenzhen_CS'; Folder = '香港中文大学深圳_计算机科学'; Cn = '香港中文大学（深圳）计算机科学理学硕士'; CnShort = '港中深_计算机科学'; EnTag = 'CUHKSZ_MSc_Computer_Science'; Pending = $false },
    [pscustomobject]@{ Index = 5; Source = '10_CUHK_HK_Robotics'; Folder = '香港中文大学_机器人学'; Cn = '香港中文大学 机器人学理学硕士'; CnShort = '香港中文大学_机器人学'; EnTag = 'CUHK_MSc_Robotics'; Pending = $false },
    [pscustomobject]@{ Index = 6; Source = '07_CityUHK_P53_CS'; Folder = '香港城市大学_计算机科学_P53'; Cn = '香港城市大学 计算机科学理学硕士（P53）'; CnShort = '香港城市大学_计算机科学'; EnTag = 'CityUHK_MSc_Computer_Science'; Pending = $false },
    [pscustomobject]@{ Index = 7; Source = '03_CityUDG_AI'; Folder = '香港城市大学东莞_人工智能'; Cn = '香港城市大学（东莞）人工智能理学硕士'; CnShort = '香港城市大学东莞_人工智能'; EnTag = 'CityUHKDG_MSc_Artificial_Intelligence'; Pending = $false },
    [pscustomobject]@{ Index = 8; Source = '06_CityUDG_CS'; Folder = '香港城市大学东莞_计算机科学'; Cn = '香港城市大学（东莞）计算机科学理学硕士'; CnShort = '香港城市大学东莞_计算机科学'; EnTag = 'CityUHKDG_MSc_Computer_Science'; Pending = $false },
    [pscustomobject]@{ Index = 9; Source = '11_UM_Robotics_and_Autonomous_Systems'; Folder = '澳门大学_机器人与自主系统'; Cn = '澳门大学 机器人与自主系统理学硕士'; CnShort = '澳门大学_机器人与自主系统'; EnTag = 'UM_MSc_Robotics_and_Autonomous_Systems'; Pending = $false },
    [pscustomobject]@{ Index = 10; Source = '12_UM_AI'; Folder = '澳门大学_人工智能'; Cn = '澳门大学 人工智能理学硕士'; CnShort = '澳门大学_人工智能'; EnTag = 'UM_MSc_Artificial_Intelligence'; Pending = $false },
    [pscustomobject]@{ Index = 11; Source = '13_MUST_AI'; Folder = '澳门科技大学_人工智能'; Cn = '澳门科技大学 人工智能理学硕士'; CnShort = '澳门科技大学_人工智能'; EnTag = 'MUST_MSc_Artificial_Intelligence'; Pending = $false },
    [pscustomobject]@{ Index = 12; Source = '12_HKUSTGZ_Embodied_Intelligence'; Folder = '香港科技大学广州_具身智能'; Cn = '香港科技大学（广州）具身智能理学硕士（暂用名称）'; CnShort = '香港科技大学广州_具身智能'; EnTag = 'HKUSTGZ_MSc_Embodied_Intelligence'; Pending = $false }
)

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Get-SingleFile {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$Filter
    )
    $files = @(Get-ChildItem -LiteralPath $Directory -File -Filter $Filter)
    if ($files.Count -ne 1) {
        throw "Expected exactly one file matching '$Filter' in '$Directory', found $($files.Count)."
    }
    return $files[0].FullName
}

function Copy-NamedFile {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )
    $parent = Split-Path -Parent $Destination
    Ensure-Directory $parent
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

Ensure-Directory $outputRoot
$schoolRoot = Join-Path $outputRoot '01_学校正式提交包'
$refereeRoot = Join-Path $outputRoot '02_推荐人核对与签字包'
$evidenceRoot = Join-Path $outputRoot '03_通用证明材料'
$pendingRoot = Join-Path $outputRoot '04_待确认项目_暂不提交'
Ensure-Directory $schoolRoot
Ensure-Directory $refereeRoot
Ensure-Directory $evidenceRoot
Ensure-Directory $pendingRoot

$academicRoot = Join-Path $refereeRoot '01_傅向华老师_学术推荐信'
$airsRoot = Join-Path $refereeRoot '02_陈淡生老师_AIRS实习推荐信'
foreach ($teacherRoot in @($academicRoot, $airsRoot)) {
    Ensure-Directory (Join-Path $teacherRoot '01_中文版_请老师核对')
    Ensure-Directory (Join-Path $teacherRoot '02_英文版_请老师签字')
    Ensure-Directory (Join-Path $teacherRoot '03_待确认项目_暂不签字')
}

$manifestRows = New-Object System.Collections.Generic.List[string]
$manifestRows.Add('| 编号 | 学校与专业 | 状态 | 正式文件 | 中文核对 | 推荐信 |')
$manifestRows.Add('|---:|---|---|---:|---:|---:|')

foreach ($program in $programs) {
    $sourceRoot = Join-Path $packageRoot $program.Source
    if (-not (Test-Path -LiteralPath $sourceRoot)) {
        throw "Missing source package: $sourceRoot"
    }

    $cvEn = Join-Path $sourceRoot '01_CV\CV_Robotics_Algorithms_Final_EN.pdf'
    $cvZh = Join-Path $sourceRoot '01_CV\CV_Robotics_Algorithms_Final_ZH.pdf'
    $psPdfRoot = Join-Path $sourceRoot '02_PS\最终PDF_修正版'
    $rlPdfRoot = Join-Path $sourceRoot '03_推荐信\最终版'
    $psMdRoot = Join-Path $sourceRoot '02_PS'
    $rlMdRoot = Join-Path $sourceRoot '03_推荐信'

    $psEnPdf = Get-SingleFile $psPdfRoot '*_EN.pdf'
    $psZhPdf = Get-SingleFile $psPdfRoot '*_ZH.pdf'
    $academicEnPdf = Get-SingleFile $rlPdfRoot 'RL_02_Academic*_EN.pdf'
    $academicZhPdf = Get-SingleFile $rlPdfRoot 'RL_02_Academic*_ZH.pdf'
    $airsEnPdf = Get-SingleFile $rlPdfRoot 'RL_01_AIRS*_EN.pdf'
    $airsZhPdf = Get-SingleFile $rlPdfRoot 'RL_01_AIRS*_ZH.pdf'

    $psEnMd = Get-SingleFile $psMdRoot '*_EN.md'
    $psZhMd = Get-SingleFile $psMdRoot '*_ZH.md'
    $academicEnMd = Get-SingleFile $rlMdRoot 'RL_02_Academic*_EN.md'
    $academicZhMd = Get-SingleFile $rlMdRoot 'RL_02_Academic*_ZH.md'
    $airsEnMd = Get-SingleFile $rlMdRoot 'RL_01_AIRS*_EN.md'
    $airsZhMd = Get-SingleFile $rlMdRoot 'RL_01_AIRS*_ZH.md'

    foreach ($required in @($cvEn, $cvZh, $psEnPdf, $psZhPdf, $academicEnPdf, $academicZhPdf, $airsEnPdf, $airsZhPdf)) {
        if (-not (Test-Path -LiteralPath $required)) {
            throw "Missing required file: $required"
        }
    }

    $folderName = ('{0:D2}_{1}' -f $program.Index, $program.Folder)
    $programRoot = if ($program.Pending) { Join-Path $pendingRoot $folderName } else { Join-Path $schoolRoot $folderName }
    $englishRoot = Join-Path $programRoot '01_英文正式文件'
    $chineseRoot = Join-Path $programRoot '02_中文核对文件'
    $sourceDraftRoot = Join-Path $programRoot '03_可编辑源稿'
    Ensure-Directory $englishRoot
    Ensure-Directory $chineseRoot
    Ensure-Directory $sourceDraftRoot

    Copy-NamedFile $cvEn (Join-Path $englishRoot '01_Yongyi_Lai_CV_EN.pdf')
    Copy-NamedFile $psEnPdf (Join-Path $englishRoot ("02_Yongyi_Lai_Personal_Statement_{0}_EN.pdf" -f $program.EnTag))
    Copy-NamedFile $academicEnPdf (Join-Path $englishRoot ("03_Yongyi_Lai_Academic_Recommendation_{0}_EN.pdf" -f $program.EnTag))
    Copy-NamedFile $airsEnPdf (Join-Path $englishRoot ("04_Yongyi_Lai_AIRS_Recommendation_{0}_EN.pdf" -f $program.EnTag))

    Copy-NamedFile $cvZh (Join-Path $chineseRoot '01_赖咏怡_简历_中文核对版.pdf')
    Copy-NamedFile $psZhPdf (Join-Path $chineseRoot ("02_赖咏怡_个人陈述_{0}_中文核对版.pdf" -f $program.CnShort))
    Copy-NamedFile $academicZhPdf (Join-Path $chineseRoot ("03_赖咏怡_学术推荐信_{0}_中文核对版.pdf" -f $program.CnShort))
    Copy-NamedFile $airsZhPdf (Join-Path $chineseRoot ("04_赖咏怡_AIRS实习推荐信_{0}_中文核对版.pdf" -f $program.CnShort))

    Copy-NamedFile $psEnMd (Join-Path $sourceDraftRoot ("01_Personal_Statement_{0}_EN.md" -f $program.EnTag))
    Copy-NamedFile $psZhMd (Join-Path $sourceDraftRoot ("02_个人陈述_{0}_中文核对版.md" -f $program.CnShort))
    Copy-NamedFile $academicEnMd (Join-Path $sourceDraftRoot ("03_Academic_Recommendation_{0}_EN.md" -f $program.EnTag))
    Copy-NamedFile $academicZhMd (Join-Path $sourceDraftRoot ("04_学术推荐信_{0}_中文核对版.md" -f $program.CnShort))
    Copy-NamedFile $airsEnMd (Join-Path $sourceDraftRoot ("05_AIRS_Recommendation_{0}_EN.md" -f $program.EnTag))
    Copy-NamedFile $airsZhMd (Join-Path $sourceDraftRoot ("06_AIRS实习推荐信_{0}_中文核对版.md" -f $program.CnShort))

    $statusText = if ($program.Pending) { '待官网确认，暂不提交/签字' } else { '材料已备齐，提交前核对系统要求' }
    $checklist = @"
# $($program.Cn) - 提交清单

## 当前状态

$statusText。

## 文件怎么用

| 文件夹 | 用途 |
|---|---|
| 01_英文正式文件 | 申请系统实际使用的英文 CV、PS 与两封英文推荐信。推荐信仅在系统允许申请人上传时自行上传；若系统要求推荐人在线提交，应将对应文件交给推荐人。 |
| 02_中文核对文件 | 仅用于本人和推荐人核对事实、准备面试，不上传英文授课项目申请系统。 |
| 03_可编辑源稿 | 后续如遇字数、格式或项目名称变化，从这里修改；不要直接改 PDF。 |

## 提交前逐项检查

- [ ] 项目官方英文名称与申请系统完全一致。
- [ ] CV 使用英文正式版。
- [ ] PS 字数和文件格式符合该项目当轮要求。
- [ ] 两封推荐信的目标学校、专业、推荐人姓名及单位无误。
- [ ] 推荐信提交方式已确认：推荐人链接 / 推荐人邮件 / 申请人上传。
- [ ] 英文成绩单、在校或预毕业证明、专业排名和雅思成绩按系统要求上传。
- [ ] 护照、证件照及系统表格已从个人证件原件补充。
- [ ] 所有 PDF 打开正常，文件名无乱码，未误传中文核对版。

## 重要提醒

推荐信的“英文正式文件”是供签字和提交的版本。不要把中文版当作正式推荐信上传。若系统直接联系推荐人，应由推荐人从本人邮箱或系统链接完成确认/提交。
"@
    if ($program.Pending) {
        $checklist += @"

## 待确认事项

港科广项目目前使用“机器人／具身智能授课型硕士”工作名称。官网正式公布后，必须核对并更新：正式中英文项目名、学位类型、所属学部、课程设置、申请轮次、推荐信要求和文书字数；完成这些核对前，本文件夹不得直接提交，也无需请老师签字。
"@
    }
    Set-Content -LiteralPath (Join-Path $programRoot '00_提交清单_请先看.md') -Value $checklist -Encoding utf8

    $teacherIndex = '{0:D2}' -f $program.Index
    if ($program.Pending) {
        $academicPending = Join-Path $academicRoot '03_待确认项目_暂不签字'
        $airsPending = Join-Path $airsRoot '03_待确认项目_暂不签字'
        Copy-NamedFile $academicZhPdf (Join-Path $academicPending ("${teacherIndex}_$($program.CnShort)_学术推荐信_中文核对版.pdf"))
        Copy-NamedFile $academicEnPdf (Join-Path $academicPending ("${teacherIndex}_$($program.EnTag)_Academic_Recommendation_EN.pdf"))
        Copy-NamedFile $airsZhPdf (Join-Path $airsPending ("${teacherIndex}_$($program.CnShort)_AIRS实习推荐信_中文核对版.pdf"))
        Copy-NamedFile $airsEnPdf (Join-Path $airsPending ("${teacherIndex}_$($program.EnTag)_AIRS_Recommendation_EN.pdf"))
    } else {
        Copy-NamedFile $academicZhPdf (Join-Path (Join-Path $academicRoot '01_中文版_请老师核对') ("${teacherIndex}_$($program.CnShort)_学术推荐信_中文核对版.pdf"))
        Copy-NamedFile $academicEnPdf (Join-Path (Join-Path $academicRoot '02_英文版_请老师签字') ("${teacherIndex}_$($program.EnTag)_Academic_Recommendation_EN.pdf"))
        Copy-NamedFile $airsZhPdf (Join-Path (Join-Path $airsRoot '01_中文版_请老师核对') ("${teacherIndex}_$($program.CnShort)_AIRS实习推荐信_中文核对版.pdf"))
        Copy-NamedFile $airsEnPdf (Join-Path (Join-Path $airsRoot '02_英文版_请老师签字') ("${teacherIndex}_$($program.EnTag)_AIRS_Recommendation_EN.pdf"))
    }

    $manifestRows.Add("| $teacherIndex | $($program.Cn) | $statusText | 4 | 4 | 2 |")
}

$academicInstructions = @"
# 傅向华老师 - 学术推荐信文件说明

傅老师您好：

感谢您愿意担任我的研究生申请推荐人。这里按学校和专业整理了推荐信，中文和英文文件使用相同编号，便于对应。

1. 请先查看 01_中文版_请老师核对，重点核对推荐关系、课程经历、评价内容、职务和邮箱等信息。
2. 如内容合适，请在 02_英文版_请老师签字 中签署相同编号的英文推荐信；如需修改，以您的意见为准。
3. 各版本主体内容基本一致，主要区别是申请学校和专业名称。
4. 部分学校会把提交链接发送到您的邮箱，届时我会提前说明对应学校和编号，尽量减少您核对文件的时间。
5. 港科广具身智能已纳入本次正式核对范围；当前使用 MSc in Embodied Intelligence / 具身智能理学硕士 作为暂用项目名称，请同时核对并签署对应编号文件。最终网申前再按官网核对正式项目名称和系统要求。

推荐人信息：傅向华，深圳技术大学人工智能学院副院长；邮箱 fuxianghua@sztu.edu.cn。电话在学校没有强制要求时不填写。
"@
Set-Content -LiteralPath (Join-Path $academicRoot '00_文件说明_请傅向华老师先看.md') -Value $academicInstructions -Encoding utf8

$airsInstructions = @"
# 陈淡生老师 - AIRS 实习推荐信文件说明

陈老师您好：

感谢您愿意担任我的研究生申请推荐人。这里按学校和专业整理了推荐信，中文和英文文件使用相同编号，便于对应。

1. 请先查看 01_中文版_请老师核对，重点核对推荐关系、实习经历、评价内容、职务和邮箱等信息。
2. 如内容合适，请在 02_英文版_请老师签字 中签署相同编号的英文推荐信；如需修改，以您的意见为准。
3. 各版本主体内容基本一致，主要区别是申请学校和专业名称。
4. 部分学校会把提交链接发送到您的邮箱，届时我会提前说明对应学校和编号，尽量减少您核对文件的时间。
5. 港科广具身智能已纳入本次正式核对范围；当前使用 MSc in Embodied Intelligence / 具身智能理学硕士 作为暂用项目名称，请同时核对并签署对应编号文件。最终网申前再按官网核对正式项目名称和系统要求。

电话在学校没有强制要求时不填写；推荐人姓名、职务、机构和邮箱以推荐信中文版中已确认的信息为准。
"@
Set-Content -LiteralPath (Join-Path $airsRoot '00_文件说明_请陈淡生老师先看.md') -Value $airsInstructions -Encoding utf8

$academicEvidenceRoot = Join-Path $evidenceRoot '01_学业与语言'
$awardRoot = Join-Path $evidenceRoot '02_竞赛与奖项'
$internshipRoot = Join-Path $evidenceRoot '03_实习证明'
$identityRoot = Join-Path $evidenceRoot '04_个人证件与照片_提交时补充'
foreach ($path in @($academicEvidenceRoot, $awardRoot, $internshipRoot, $identityRoot)) { Ensure-Directory $path }

$academicSources = @(
    @{ Source = '02_材料证据\04_学业证明\赖咏怡-202300202024-中英文成绩单\赖咏怡-202300202024-英文成绩单.pdf'; Name = '01_Yongyi_Lai_Official_Transcript_EN.pdf' },
    @{ Source = '02_材料证据\04_学业证明\赖咏怡-202300202024-中英文成绩单\赖咏怡-202300202024-中文成绩单.pdf'; Name = '02_赖咏怡_官方成绩单_中文.pdf' },
    @{ Source = '02_材料证据\04_学业证明\在校证明.pdf'; Name = '03_赖咏怡_在校证明.pdf' },
    @{ Source = '02_材料证据\04_学业证明\预毕业证明.pdf'; Name = '04_赖咏怡_预毕业证明.pdf' },
    @{ Source = '02_材料证据\04_学业证明\专业排名.pdf'; Name = '05_赖咏怡_专业排名证明.pdf' },
    @{ Source = '02_材料证据\04_学业证明\成绩证明.pdf'; Name = '06_赖咏怡_成绩证明.pdf' },
    @{ Source = '02_材料证据\04_学业证明\成绩对照表.pdf'; Name = '07_深圳技术大学_成绩等级对照表.pdf' },
    @{ Source = '02_材料证据\05_雅思成绩\电子成绩单-6.5.pdf'; Name = '08_Yongyi_Lai_IELTS_Academic_6.5.pdf' }
)
foreach ($item in $academicSources) {
    $sourcePath = Join-Path $workspaceRoot $item.Source
    if (Test-Path -LiteralPath $sourcePath) {
        Copy-NamedFile $sourcePath (Join-Path $academicEvidenceRoot $item.Name)
    }
}

$awardSources = @(
    @{ Source = '02_材料证据\03_获奖证书\RoboMaster对抗赛竞技三等奖.pdf'; Name = '01_RoboMaster_2025_全国赛三等奖.pdf' },
    @{ Source = '02_材料证据\03_获奖证书\RoboMaster联盟赛竞技二等奖.pdf'; Name = '02_RoboMaster_2025_高校联盟赛二等奖.pdf' },
    @{ Source = '02_材料证据\03_获奖证书\华为ICT深圳赛区一等奖.pdf'; Name = '03_华为ICT_OpenHarmony_省赛一等奖.pdf' },
    @{ Source = '02_材料证据\03_获奖证书\华为ICT大赛国三证书.pdf'; Name = '04_华为ICT_OpenHarmony_中国总决赛三等奖.pdf' }
)
foreach ($item in $awardSources) {
    $sourcePath = Join-Path $workspaceRoot $item.Source
    if (Test-Path -LiteralPath $sourcePath) {
        Copy-NamedFile $sourcePath (Join-Path $awardRoot $item.Name)
    }
}

$airsOffer = Join-Path $workspaceRoot 'AIRS实习生录用通知书（赖咏怡）.pdf'
if (Test-Path -LiteralPath $airsOffer) {
    Copy-NamedFile $airsOffer (Join-Path $internshipRoot '01_赖咏怡_AIRS实习生录用通知书.pdf')
}

$photoSource = 'F:\照片\证件照2.jpg'
if (Test-Path -LiteralPath $photoSource) {
    Copy-NamedFile $photoSource (Join-Path $identityRoot '01_赖咏怡_证件照.jpg')
}

$identityReadme = @"
# 个人证件与照片

本目录只保存证件照副本。以下材料含敏感个人信息，不在公共整理包中重复复制，请在具体申请系统要求时从个人原件上传：

- 护照资料页；
- 身份证正反面（仅在系统明确要求时）；
- 港澳通行证或其他出入境证件（如学校要求）；
- 电子签名或推荐人签名文件（不要与普通申请资料混存）。

上传前请逐项核对姓名拼音、证件号码、有效期和文件清晰度。
"@
Set-Content -LiteralPath (Join-Path $identityRoot '00_个人证件补充说明.md') -Value $identityReadme -Encoding utf8

$evidenceReadme = @"
# 通用证明材料清单

本目录集中放置各学校可能共用的证明材料，避免在每个学校文件夹重复保存。

## 已整理

- 英文、中文正式成绩单；
- 在校证明、预毕业证明、专业排名证明；
- 成绩证明与成绩等级对照表；
- 雅思 Academic 6.5 成绩单；
- RoboMaster 与华为 ICT 竞赛证明；
- AIRS 实习录用通知；
- 证件照（若原文件存在）。

## 提交原则

1. 以申请系统字段为准，不要把整个目录一次性上传。
2. 英文授课项目优先上传英文成绩单；系统要求时再补中文原件。
3. 奖项证明只在系统设有 Awards / Supporting Documents 栏目或确有帮助时上传。
4. 护照、身份证等敏感资料从个人原件按需上传，不在本整理包重复保存。
5. 若学校要求“官方成绩单由学校直接发送”，此处 PDF 只能用于网申预审，不能替代学校直送。
"@
Set-Content -LiteralPath (Join-Path $evidenceRoot '00_通用证明材料清单_请先看.md') -Value $evidenceReadme -Encoding utf8

$overviewRows = $manifestRows -join "`r`n"
$overview = @"
# 2027 Fall 最终提交与推荐人确认包

## 从这里开始

本目录是从 00_当前申请/02_学校提交包 导出的清晰使用版。原始定稿文件没有被覆盖或删除。目录按实际使用对象分为四部分：

1. 01_学校正式提交包：11 个申请专业；每个专业均含英文正式文件、中文核对文件、可编辑源稿和提交清单。
2. 02_推荐人核对与签字包：分别给傅向华老师和陈淡生老师；中文先核对、英文后签字，编号一一对应。
3. 03_通用证明材料：成绩单、在校／预毕业证明、排名、雅思、奖项和实习证明。
4. 04_待确认项目_暂不提交：预留给未来仍未确认的项目；港科广具身智能材料已转入正式提交包，但名称仍需在网申前按官网核对。

## 专业与材料状态

$overviewRows

## 使用顺序

1. 进入对应专业，先看 00_提交清单_请先看.md。
2. 用中文核对版检查事实、专业名称和个人贡献；正式上传只使用英文正式文件。
3. 推荐信按申请系统要求处理：系统若联系推荐人，则把同编号英文签字版交给相应老师；仅在系统明确允许时由申请人自行上传。
4. 从通用证明材料中按系统字段选择文件，不要整包上传。
5. 最后检查文件预览、页面完整性、项目名称、截止时间和缴费状态。

## 命名规则

- 学校文件夹使用“序号 + 中文学校名 + 专业名”，便于申请时快速定位。
- 英文正式文件使用申请人英文名与完整项目标签，便于网申系统识别。
- 中文文件明确标注“中文核对版”，防止误传。
- 推荐人文件使用同一编号对齐中英文，老师无需在多份文件中猜测对应关系。

## 仍需本人按系统动态补充

- 网申表中的个人信息、教育经历和实习经历；
- 护照等个人证件；
- 推荐人系统信息与推荐链接；
- 申请费支付凭证；
- 个别项目临时新增的写作题、课程描述或补充表格；
- 港科广具身智能项目的正式名称、申请入口和材料要求；当前材料已可先交推荐人核对和签字。
"@
Set-Content -LiteralPath (Join-Path $outputRoot '00_总览_从这里开始.md') -Value $overview -Encoding utf8

# PowerShell treats a Markdown backtick followed by 0 as an escape sequence
# inside here-strings.  Remove any resulting NUL characters from generated
# Markdown so generated paths remain readable.
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
Get-ChildItem -LiteralPath $outputRoot -Recurse -File -Filter '*.md' | ForEach-Object {
    $text = [System.IO.File]::ReadAllText($_.FullName)
    if ($text.IndexOf([char]0) -ge 0) {
        [System.IO.File]::WriteAllText($_.FullName, $text.Replace(([char]0).ToString(), ''), $utf8NoBom)
    }
}

$pdfFiles = @(Get-ChildItem -LiteralPath $outputRoot -Recurse -File -Filter '*.pdf')
$mdFiles = @(Get-ChildItem -LiteralPath $outputRoot -Recurse -File -Filter '*.md')
$summary = [pscustomobject]@{
    OutputRoot = $outputRoot
    Programs = $programs.Count
    ConfirmedPrograms = @($programs | Where-Object { -not $_.Pending }).Count
    PendingPrograms = @($programs | Where-Object { $_.Pending }).Count
    PdfFiles = $pdfFiles.Count
    MarkdownFiles = $mdFiles.Count
}
$summary | Format-List
