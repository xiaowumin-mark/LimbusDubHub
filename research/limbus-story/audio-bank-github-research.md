# Limbus Company 音频 bank 与替换项目调研

调研日期：2026-06-22

## 结论

目前在 GitHub 上找到了 Limbus Company 专用的音频替换项目，但没有找到一个成熟的、专门针对 Limbus Company 的 `.bank` 解码并完整重打包项目。

对社区配音来说，优先级建议是：

1. 先走运行时 `.wav` 替换路线，不碰游戏原始 `.bank`。
2. 如果已经能制作兼容 `.bank`，再考虑用 mod loader 挂载/替换同名 `.bank`。
3. 通用 FSB5 / FMOD bank 工具适合抽样、验证、提取参考音频；不要默认它们能保持 Limbus 原 bank 的事件 GUID、事件路径、参数、同步点和演出逻辑。

## Limbus 专用项目

| 项目 | 类型 | 对配音项目的价值 | 备注 |
| --- | --- | --- | --- |
| [kimght/LimbusCustomSound](https://github.com/kimght/LimbusCustomSound) | BepInEx IL2CPP 运行时替换 | 推荐优先试用。按 FMOD 事件路径放置 `.wav`，例如 `event:/Voice/Default/D_Wick` 对应 `Sound/Voice/Default/D_Wick.wav`。 | 不解析 `.bank`，而是在运行时拦截 FMOD 事件并播放外部 `.wav`。README 写明音效和语音可替换，音量控制尚未完善。 |
| [LEAGUE-OF-NINE/LimbusCustomSoundPlus](https://github.com/LEAGUE-OF-NINE/LimbusCustomSoundPlus) | `LimbusCustomSound` fork | 增加了缺失 `Sound` 目录自动创建、`.wav` 存在性/格式检查、BGM 释放和循环处理。 | 仍然是 `.wav` 运行时替换，不是 bank 解码。源码里声音类型匹配使用 `BGM/`、`VOICE/`、`SFX/`，大小写和实际事件路径需要实测。 |
| [LEAGUE-OF-NINE/LimbusModLoader](https://github.com/LEAGUE-OF-NINE/LimbusModLoader) | Limbus mod loader，支持 sound mods | 如果手里已经有可用的改造 `.bank`，可以把 `.bank` 放进 `%AppData%\LimbusCompanyMods`。 | README 说明 Sound Mods 是 `.bank` 文件；源码 `sound.py` 会在校验后替换 `%AppData%/../LocalLow/ProjectMoon/LimbusCompany/Assets/Sound/FMODBuilds/Desktop` 下的同名 `.bank`，并用 `.bak` 备份。它不负责生成或解码 `.bank`。 |

## LimbusCustomSound 的替换机制

源码确认它的核心不是改游戏文件，而是 patch FMOD 调用：

- `RuntimeManager.CreateInstance(FMOD.GUID)`：通过 GUID 查事件路径。
- `SoundManager.HasReplacement(eventPath)`：检查 `Sound/` 目录里是否存在同路径 `.wav`。
- `FMOD.Studio.EventInstance.start`：把原事件音量设为 0，再启动外部 `.wav`。
- `setVolume`、`setPaused`、`stop`、`release`：同步外部 `.wav` 的暂停、停止和释放。
- `SoundManager.GetEventLength`：把替换 `.wav` 的长度回传给游戏。
- `VoiceGenerator.SetMainVoice`：专门处理主语音事件，避免多条主语音重叠。

文件映射规则非常直接：

```text
event:/Voice/Default/D_Wick
=> BepInEx/plugins/LimbusCustomSound/Sound/Voice/Default/D_Wick.wav
```

这条路线最适合社区配音包：我们只需要拿到事件路径，然后生成同路径 `.wav`，不必重建 FMOD bank。

## 通用 bank / FSB 工具

| 项目 | 能做什么 | 限制 |
| --- | --- | --- |
| [HearthSim/python-fsb5](https://github.com/HearthSim/python-fsb5) | 提取 FSB5 / FMOD Sample Bank，支持 MPEG、Vorbis、WAVE 等样本。 | 主要是 sample 提取，不是完整 FMOD Studio bank 重建工具。 |
| [astral4/fsbex](https://github.com/astral4/fsbex) | Rust FSB5 提取库，可从 FMOD sound banks 提取音频流。 | 只支持 FSB5；偏库用途，不是 Limbus 专用替换方案。 |
| [IZH318/FSB-BANK-Extractor-Rebuilder](https://github.com/IZH318/FSB-BANK-Extractor-Rebuilder) | GUI/CLI 工具，说明中提到支持 `.fsb` 和 `.bank` 音频流提取，并提供 rebuild 功能。 | 不是 Limbus 专用；能否保持 Limbus 所需的事件结构和 runtime 兼容性必须用小 bank 实测。 |
| [Wouldubeinta/Fmod-Bank-Tools](https://github.com/Wouldubeinta/Fmod-Bank-Tools) | Qt GUI 工具，支持从 FMOD `.bank` 中提取 FSB5，再用 FSBank 重建 FSB 并塞回 bank。 | 对 Limbus 有试验价值，重点应测试 `.assets.bank`。它要求替换音频保持相同文件类型、码率等，并且时长小于等于原音频；不是完整还原 FMOD Studio 工程的工具。 |

## Fmod-Bank-Tools 对 Limbus 的适配判断

源码确认 `Fmod-Bank-Tools` 的流程是：

1. 读取 `.bank` 的 `RIFF` / `FEV ` / `LIST` / `PROJBNKI` 结构。
2. 在 `SNDH` 块中读取内嵌 FSB 的 offset 和 size。
3. 把 `SND ` 块里的 FSB5 数据导出到工具目录的 `fsb/`。
4. 用 FMOD Core API 打开 FSB，按 subsound 导出 PCM `.wav`，并写一个同目录 `.txt` 列表记录顺序。
5. Rebuild 时读取 `.txt` 列表，用 FSBank 重新生成 FSB5。
6. 复制原 bank 的 FSB 前方 header，更新 `SNDH` 里的 FSB offset/size，再写入新的 `SND ` + FSB 数据。

我对本机 Limbus 样本做了只读文件头检查：

| 文件 | 结果 |
| --- | --- |
| `1D101A.bank` | 有 `RIFF` / `FEV ` / `SNDH`，但没有 `FSB5` / `SND `；更像事件/元数据 bank。 |
| `1D101A.assets.bank` | 有 `RIFF` / `FEV ` / `SNDH` / `SND ` / `FSB5`；更符合 `Fmod-Bank-Tools` 的提取/重建目标。 |
| `Voice_Default_0.assets.bank` | 文件头同样是 `RIFF` / `FEV `，体积很大，属于实际音频 sample bank。 |

因此，如果用这个工具测试边狱巴士，第一目标应是同名的 `.assets.bank`，不是小体积的 `.bank`。同名 `.bank` 仍然需要保留，因为它包含事件和元数据；`.assets.bank` 替换后要和原 `.bank` 的事件引用继续匹配。

风险点：

- Rebuild 并不会重建 FMOD Studio 事件图，只替换/重组 FSB sample 数据。
- README 要求新音频时长必须小于等于原音频；超长台词可能导致截断、错位或事件长度不匹配。
- 默认重建格式是 Vorbis，质量 75；要确认原 Limbus bank 的编码、采样率、声道是否接近。
- 如果替换后 FSB 内 subsound 数量、顺序、文件名或同步点发生变化，原事件可能找不到对应 sample。
- 需要用一个很小的剧情 `.assets.bank` 做提取、原样重建、替换测试。先验证“原样 extract -> rebuild 后游戏能播”，再换入新配音。

### 1D101A.assets.bank 原样重打包测试

用户已在 `test/` 目录完成一次 `1D101A.assets.bank` 的 extract/rebuild。该目录包含原始 bank、解包 wav、重建 FSB 和 rebuilt bank。`test/` 已加入 `.gitignore`，避免误提交原始或重建后的游戏音频数据。

截图配置：

- Format: `Vorbis`
- Quality: `100`
- CPU Thread: `2`
- `Default settings` 勾选
- `Encode sync point`、`Enable looping`、`Embeded file name`、`Write peak volume` 勾选

注意：从 `Fmod-Bank-Tools` 源码看，`Default settings` 为 true 时，重建 flags 使用 `FSBANK_BUILD_DEFAULT`；下方 sync point / looping / embedded names / peak volume 这些开关只有在 `Default settings` 为 false 时才会参与自定义 flags。

只读结构检查结果：

| 项目 | 原始 `1D101A.assets.bank` | rebuilt `1D101A.assets.bank` |
| --- | ---: | ---: |
| 文件大小 | 939648 | 938048 |
| `RIFF` size | 939640 | 938040 |
| `SNDH` offset | 706 | 706 |
| `SNDH` FSB offset | 960 | 960 |
| `SNDH` FSB size | 938688 | 937088 |
| `SND ` offset | 926 | 926 |
| `SND ` chunk size | 938714 | 937114 |
| `FSB5` offset | 960 | 960 |
| FSB version | 1 | 1 |
| FSB subsound count | 7 | 7 |

解包出的 wav 均为 `pcm_s16le`、`48000 Hz`、单声道、16-bit。时长：

| 文件 | 时长 |
| --- | ---: |
| `1D101A-02.wav` | 4.336 s |
| `1D101A-03.wav` | 7.114667 s |
| `1D101A-04.wav` | 8.000 s |
| `1D101A-05.wav` | 0.800 s |
| `1D101A-06.wav` | 5.712 s |
| `1D101A-07.wav` | 5.477333 s |
| `1D101A-08.wav` | 4.304 s |

`1D101A.assets[0].txt` 中的 subsound 顺序是：

```text
1D101A-07.wav
1D101A-04.wav
1D101A-02.wav
1D101A-03.wav
1D101A-06.wav
1D101A-05.wav
1D101A-08.wav
```

这个顺序在原始 bank 和 rebuilt bank 的内嵌名字表中一致，因此后续替换配音时不要按文件名排序重写该 txt；应保留工具导出的顺序。

当前结论：原样 rebuild 在静态结构上通过，并已进游戏完成 runtime 验证。用户反馈 rebuilt `1D101A.assets.bank` 可以在游戏中正常使用，没有播放、加载或流程问题。

这说明 `Fmod-Bank-Tools` 对 `1D101A.assets.bank` 的原样 extract/rebuild 路线可作为后续配音替换实验基准。

用户后续又完成了替换音频测试：替换解包后的 wav、重建 `.assets.bank` 后，游戏可以正常加载和播放，没有检测或拒绝替换后的音频文件。基于该样本，README 中“新音频时长必须小于等于原音频”的限制至少不是游戏侧硬校验；但为了降低批量制作风险，仍建议保留 FSB 内 subsound 数量、文件名、`1D101A.assets[0].txt` 顺序和单声道/采样率等基础格式一致性。

## 对本项目的建议路线

1. 用 `LimbusCustomSound` 路线做第一版原型：启动游戏后让插件打印所有播放事件路径，记录剧情播放时触发的 `event:/...`。
2. 把事件路径和我们已有的 `analysis/story-audio-map.csv` 合并，做一张“剧情行/剧情 ID -> FMOD 事件路径 -> wav 文件路径”的配音表。
3. 以一段短剧情做试点，只放外部 `.wav`，验证字幕推进、音量、暂停、跳过、回放是否正常。
4. 并行做一个 `Fmod-Bank-Tools` 小样本实验：复制 `1D101A.assets.bank` 到独立 staging 目录，先原样 extract/rebuild，再通过 mod loader 或备份覆盖方式测试。
5. 若 `.wav` 替换路线可用，发布社区包时优先发布 `Sound/Voice/.../*.wav` 和安装说明，避免分发或覆盖原游戏 `.bank`。
6. 只有在需要保持 FMOD 事件内部逻辑、参数或混音结构时，再研究 `.bank` 生成。此时应优先新建测试 bank，不要直接改 Steam 游戏目录。

## fmod-bank-helper CLI/DLL 验收

验收日期：2026-06-22

已从 `E:\projects\Fmod-Bank-Tools\build-msvc` 复制以下运行产物到本项目 `tools/fmod-bank-helper/`：

- `fmod-bank-helper.exe`
- `fmod_bank_helper_c_api.dll`
- `fmod64.dll`
- `fsbank64.dll`
- `libfsbvorbis64.dll`

`tools/fmod-bank-helper/` 已加入 `.gitignore`，避免把 native 二进制和 FMOD/FSBank runtime DLL 误提交。

验收样本：

- `test/1D101A.assets.bank`
- `E:\projects\Fmod-Bank-Tools\test-bank-data\S001B.assets.bank`，仅复制到 `test/helper-batch-validation-*` 目录做批量测试

CLI 单文件链路：

| 命令 | 结果 |
| --- | --- |
| `inspect --bank test/1D101A.assets.bank --json` | 通过；识别 `fsbCount=1`、`subsoundCount=7`、embedded names 顺序为 `1D101A-07, 1D101A-04, 1D101A-02, 1D101A-03, 1D101A-06, 1D101A-05, 1D101A-08`。 |
| `extract --bank test/1D101A.assets.bank --out ... --json` | 通过；导出 1 个 FSB 和 7 个 wav，txt 顺序保持 subsound 顺序。 |
| `rebuild --bank ... --wav-dir ... --list ... --out ... --format vorbis --quality 100 --json` | 通过；rebuilt bank 可再次 inspect，`subsoundCount=7`、`SNDH/SND/FSB5` 均存在。 |

CLI 批量链路：

| 命令 | 结果 |
| --- | --- |
| `batch-extract --input-dir ... --out-dir ... --jobs 2 --json` | 通过；2 个 bank 均成功。 |
| `batch-rebuild --input-dir ... --wav-root ... --out-dir ... --jobs 2 --format vorbis --quality 100 --json` | 通过；2 个 bank 均成功。rebuilt `1D101A.assets.bank` 为 7 条 subsound，rebuilt `S001B.assets.bank` 为 59 条 subsound。 |

C API DLL 链路：

| 函数 | 结果 |
| --- | --- |
| `fbh_inspect_bank` | 通过；返回码 `0`，JSON `success=true`，正确识别 `1D101A.assets.bank` 的 7 条 subsound。 |
| `fbh_extract_bank` | 通过；返回码 `0`，导出 7 个 wav。 |
| `fbh_rebuild_bank` | 通过；返回码 `0`，生成 rebuilt `1D101A.assets.bank`。 |

验收观察：

- 复制后的 exe/dll 可以在本项目目录独立运行，不依赖原 `Fmod-Bank-Tools` 工作目录。
- batch JSON 的作业数组字段名为 `jobs`。该字段名已作为当前稳定输出保留，Go 侧应按 `jobs` 解析。
- `--help` 已补全扩展参数，包括 `--cpu-threads`、`--default-settings`、`--encode-sync-point`、`--looping`、`--embedded-file-names`、`--write-peak-volume`、`--cache-dir`、`--password`。

### fmod-bank-helper 二次验收

验收日期：2026-06-22

用户已处理第一次验收发现的两个点：

- README 明确说明 batch summary 使用 `jobs` 数组，并保持该字段不改。
- `--help` 补全了 rebuild 扩展参数。

重新复制 `E:\projects\Fmod-Bank-Tools\build-msvc` 里的新版产物到 `tools/fmod-bank-helper/`，其中 `fmod-bank-helper.exe` 大小为 `225792` bytes，时间戳为 `2026/6/22 23:08:48`。

复验结果：

| 项目 | 结果 |
| --- | --- |
| `fmod-bank-helper.exe --help` | 通过；扩展参数和 “Batch summaries use a jobs array.” 均已出现。 |
| 单文件 `inspect/extract/rebuild` | 通过；`1D101A.assets.bank` 导出 7 个 wav，txt 顺序仍为 `1D101A-07, 1D101A-04, 1D101A-02, 1D101A-03, 1D101A-06, 1D101A-05, 1D101A-08`，rebuilt bank 再次 inspect 为 7 条 subsound。 |
| `batch-extract --jobs 2` | 通过；2 个 bank 均成功，JSON 包含 `jobs` 字段，未出现 `results` 字段。 |
| `batch-rebuild --jobs 2` | 通过；2 个 bank 均成功，rebuilt `1D101A.assets.bank` 为 7 条 subsound，rebuilt `S001B.assets.bank` 为 59 条 subsound。 |
| C API `fbh_inspect_bank` / `fbh_extract_bank` / `fbh_rebuild_bank` | 通过；三者返回码均为 `0`，C API rebuild 结果为 7 条 subsound。 |

当前结论：CLI helper 与预留 DLL/C API 均通过本项目样本回归验收，可进入 Go 侧集成阶段。

### fmod-bank-helper 三次验收

验收日期：2026-06-22

本轮重新覆盖复制 `E:\projects\Fmod-Bank-Tools\build-msvc` 中的当前产物到 `tools/fmod-bank-helper/`，并直接使用本项目目录下的 exe/dll 验证。

验证结果：

| 项目 | 结果 |
| --- | --- |
| README / CLI 文案 | 通过；README 已说明 batch JSON summary 使用 `jobs` 数组，`fmod-bank-helper.exe --help` 已列出 `--cpu-threads`、`--default-settings`、`--encode-sync-point`、`--looping`、`--embedded-file-names`、`--write-peak-volume`、`--cache-dir`、`--password`，并包含 “Batch summaries use a jobs array.” |
| `g++ -fsyntax-only src/cli/main.cpp` | 通过。 |
| 单文件 `inspect/extract/rebuild` | 通过；`test/1D101A.assets.bank` 输入为 7 条 subsound，extract JSON 返回 `listPath`，导出 7 个 wav，顺序为 `1D101A-07, 1D101A-04, 1D101A-02, 1D101A-03, 1D101A-06, 1D101A-05, 1D101A-08`，rebuilt bank 再次 inspect 为 7 条 subsound，大小为 `938048` bytes。输出目录：`test/helper-acceptance-verify3/`。 |
| `batch-extract --jobs 2` | 通过；`1D101A.assets.bank` 与 `S001B.assets.bank` 两个 job 均成功，JSON 顶层包含 `jobs`，不包含 `results`。 |
| `batch-rebuild --jobs 2` | 通过；两个 job 均成功，rebuilt `1D101A.assets.bank` 为 7 条 subsound，rebuilt `S001B.assets.bank` 为 59 条 subsound。输出目录：`test/helper-batch-acceptance-verify2/`。 |
| C API DLL | 通过；从 `tools/fmod-bank-helper/fmod_bank_helper_c_api.dll` 直接调用 `fbh_inspect_bank`、`fbh_extract_bank`、`fbh_rebuild_bank`，三者返回码均为 `0`，C API rebuild 结果为 7 条 subsound。输出目录：`test/helper-capi-acceptance-verify2/`。 |

备注：本轮 Codex 普通 PowerShell 环境未找到 `cmake` 命令，因此没有在该 shell 内重跑 MSVC build；验收对象为用户已构建并复制过来的当前 `build-msvc` 产物。

## 来源

- <https://github.com/kimght/LimbusCustomSound>
- <https://github.com/LEAGUE-OF-NINE/LimbusCustomSoundPlus>
- <https://github.com/LEAGUE-OF-NINE/LimbusModLoader>
- <https://github.com/HearthSim/python-fsb5>
- <https://github.com/astral4/fsbex>
- <https://github.com/IZH318/FSB-BANK-Extractor-Rebuilder>
- <https://github.com/Wouldubeinta/Fmod-Bank-Tools>
