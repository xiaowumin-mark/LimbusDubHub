# Limbus Company 剧情与配音资源分析

本目录保存的是本地分析副本与索引。游戏安装目录只被读取，没有写回修改。

## 来源

- 游戏目录：`E:\Program Files (x86)\Steam\steamapps\common\Limbus Company`
- Steam AppID：`1973530`
- 当前 build id：`23703681`
- 剧情文本来源：`LimbusCompany_Data\Assets\Resources_moved\Localize`
- 配音/音效 bank 来源：`LimbusCompany_Data\StreamingAssets\Assets\Sound\FMODBuilds\Desktop`
- FMOD 运行库：`fmodstudio.dll`，版本 `2.2.26`

原始剧情 JSON 已复制到 `source-copy/Localize`。该目录和 `.bank` 样本已在项目 `.gitignore` 中排除，避免误提交游戏原文或音频元数据。

## 目录内容

- `source-copy/Localize/{kr,en,jp}/StoryData/`：三语逐句剧情文本副本。
- `source-copy/Localize/{kr,en,jp}/root-story-metadata/`：剧场、关卡节点、章节、剧情 UI 等元数据副本。
- `source-copy/Localize/etc/VoiceTable.json`：战斗/人格语音相关 key 表。
- `source-copy/Localize/RemoteLocalizeFileList.json`：本地化文件分组清单。
- `audio-index/fmod_desktop_banks.csv`：`FMODBuilds\Desktop` 下全部 bank 文件索引，只记录文件名、大小、类型。
- `audio-index/samples/`：少量 `.bank` 元数据样本，不含大体积 `.assets.bank`。
- `analysis/*.csv` 和 `analysis/story-analysis-summary.json`：统计结果。
- `tools/copy_story_files.ps1`：重新复制剧情副本和音频索引。
- `tools/analyze_story_data.py`：重新生成结构统计。

## 重新生成

```powershell
powershell -ExecutionPolicy Bypass -File .\research\limbus-story\tools\copy_story_files.ps1
python .\research\limbus-story\tools\analyze_story_data.py
```

如果游戏安装在其它目录，传入 `-GameRoot`：

```powershell
powershell -ExecutionPolicy Bypass -File .\research\limbus-story\tools\copy_story_files.ps1 -GameRoot "D:\SteamLibrary\steamapps\common\Limbus Company"
```

## 剧情文件结构

逐句剧情文本是 UTF-8 JSON。Windows PowerShell 默认编码可能把韩文读成乱码，读取时要显式使用 UTF-8；Python 侧建议使用 `utf-8-sig` 兼容少量带 BOM 的文件。

典型结构：

```json
{
  "dataList": [
    {
      "id": 1,
      "model": "角色内部名或显示名",
      "teller": "显示说话人",
      "title": "称号",
      "place": "地点",
      "content": "台词或旁白"
    }
  ]
}
```

字段统计：

| 字段 | 含义 | 备注 |
| --- | --- | --- |
| `id` | 行 id | 不是所有条目都有，配音触发很可能依赖它和剧情 ID。 |
| `content` | 台词/旁白正文 | 包含富文本标签，如 `<i>`、`<color=...>`。 |
| `model` | 立绘/角色模型名 | 韩文名为主，三语文件中也常保留韩文 model。 |
| `teller` | UI 显示说话人 | 有本地化。 |
| `title` | 说话人称号/身份 | 有本地化。 |
| `place` | 地点提示 | 通常只在场景切换或段落开始出现。 |
| `d` | 少量特殊控制字段 | 只出现 183 次，需要逐例看上下文。 |
| `characterlist` | 少量角色列表字段 | 当前只在 JP 副本中统计到。 |

剧情 ID 来自文件名去掉语言前缀：`KR_1D101A.json`、`EN_1D101A.json`、`JP_1D101A.json` 对应同一个 `story_id=1D101A`。

## 当前统计

| 语言 | StoryData 文件 | dataList 条目 |
| --- | ---: | ---: |
| KR | 914 | 58091 |
| EN | 917 | 58299 |
| JP | 919 | 58612 |

唯一剧情 ID 共 919 个，三语都存在的有 914 个。覆盖差异：

- `3D309I`：KR 缺失，EN/JP 存在。
- `ProjectGS`：KR 缺失，EN/JP 存在。
- `S101B_TEST_DoNotTranslate`：仅 JP 存在。
- `S101B_TEST_DonotTranslate2`：仅 JP 存在。
- `S908A`：KR 缺失，EN/JP 存在。

按 ID 前缀分组：

| 组 | KR | EN | JP | 观察 |
| --- | ---: | ---: | ---: | --- |
| `D` | 147 | 148 | 148 | 主线/地下城式剧情 ID，常见同名语音 bank。 |
| `S` | 343 | 344 | 346 | 关卡/故事节点式剧情 ID，常见同名语音 bank。 |
| `E` | 202 | 202 | 202 | 活动/事件式剧情 ID，部分有同名语音 bank。 |
| `ES` | 35 | 35 | 35 | 当前无同名剧情语音 bank。 |
| `P` | 168 | 169 | 169 | 人格故事/资料类文本，当前无同名剧情语音 bank。 |
| `PC` | 19 | 19 | 19 | 人格相关补充文本，当前无同名剧情语音 bank。 |

## 配音资源结构

`FMODBuilds\Desktop` 下当前索引到 1527 个文件：

- 764 个 `.bank`：FMOD 事件/元数据。
- 763 个 `.assets.bank`：FMOD sample data，实际音频数据通常在这里。
- 唯一无成对 `.assets.bank` 的是 `Master.strings.bank`。

对剧情 ID 做同名匹配，919 个唯一剧情 ID 中有 640 个存在同名 `.bank` + `.assets.bank` 配对。匹配分布：

| 组 | 有同名 bank 配对 | 无同名 bank 配对 |
| --- | ---: | ---: |
| `D` | 146 | 2 |
| `S` | 344 | 2 |
| `E` | 150 | 52 |
| `ES` | 0 | 35 |
| `P` | 0 | 169 |
| `PC` | 0 | 19 |

因此，社区配音优先目标应从 `D`、`S` 和有配对的 `E` 剧情开始；`P/PC/ES` 不能假设存在同名剧情配音 bank。

## 替换配音的结论

剧情 JSON 本身没有 `voice`、`sound` 或 `audio` 字段。替换配音不应从改剧情 JSON 入手；JSON 主要决定文本、说话人、地点和演出解析信息。

当前最直接的替换面是 FMOD bank：

1. 目标路径是 `LimbusCompany_Data\StreamingAssets\Assets\Sound\FMODBuilds\Desktop`。
2. 对有同名配对的剧情，替换 `<story_id>.bank` 和 `<story_id>.assets.bank`，例如 `1D101A.bank` + `1D101A.assets.bank`。
3. bank 必须兼容 FMOD Studio Runtime `2.2.26`。
4. 仅保持文件名还不一定够。游戏可能按事件 GUID、事件路径或内部事件表触发台词；样本 `.bank` 没有暴露可读事件路径，说明需要尽量保留原 bank 的事件结构，或在运行时把游戏请求重定向到自定义事件。
5. 原游戏目录不要直接作为制作目录。先在项目或单独 staging 目录生成 bank，测试时再用备份/覆盖或 hook 方式加载。

更适合发布社区配音包的方案是运行时重定向：

- 使用 IL2CPP/BepInEx 类 mod 或同等注入层，拦截 FMOD bank 加载路径。
- metadata 中能看到 `FMODBanks`、`FMODMasterBanks`、`SoundManager.LoadBankFromAddressable`、`FMODCustomTrack_Voice_Event`、`StorySoundController` 等符号，说明可以围绕 bank 加载或 story voice track 做 hook。
- 这样可以把自制 bank 放在项目/Mod 目录，不覆盖 Steam 安装目录，也更容易随游戏更新回滚。

## 建议的制作流程

1. 用 `analysis/story-audio-map.csv` 选一个有 bank 配对且台词少的剧情 ID 做试点。
2. 以原 bank 文件名建立同名 FMOD bank，保持 bank 名、事件数量和触发顺序尽量一致。
3. 音频导出时优先沿用原采样率/声道策略，避免体积和加载行为差异过大。
4. 在独立 staging 目录验证生成的 `.bank` + `.assets.bank`。
5. 测试加载方式优先使用 hook/重定向；若临时覆盖本地游戏文件，必须先备份原 bank，并避免让 Steam 校验覆盖你的实验文件。
6. 测试后记录 `story_id`、替换 bank、台词行范围、角色分配、音频文件源和验证结果。

## 关键文件

- 剧情结构总表：`analysis/story-file-stats.csv`
- 字段统计：`analysis/story-field-stats.csv`
- 三语覆盖：`analysis/story-language-coverage.csv`
- 剧情 ID 到 FMOD bank 对应：`analysis/story-audio-map.csv`
- FMOD bank 全量索引：`audio-index/fmod_desktop_banks.csv`
