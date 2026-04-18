# PDF 解析对比测试

使用与线上一致的两种抽取方式（`app.services.parsers.pdf_text_extract`）：

1. **OpenDataLoader**（`format=text`，需本机 **Java 11+**）
2. **pdfplumber**（逐页 `extract_text`）

## 运行

在仓库根目录，建议使用 backend 虚拟环境（已安装 `opendataloader-pdf`、`pdfplumber`）：

```bash
source backend/venv/bin/activate
python test-pdf/compare_parse.py
```

默认读取 `test-pdf/test.pdf`，结果写入 **`test-pdf/out/`**：

| 文件 | 说明 |
|------|------|
| `*_opendataloader.txt` | OpenDataLoader 全文 |
| `*_pdfplumber.txt` | pdfplumber 全文 |
| `*_benchmark.json` | 耗时、字节数、路径等结构化数据 |
| `*_benchmark_summary.txt` | 人类可读的摘要 |

## 参数示例

```bash
# 指定 PDF、每种方式跑 3 次（观察 JVM 冷启动与稳定耗时）
python test-pdf/compare_parse.py --pdf test-pdf/test.pdf --runs 3
```

`--runs` 大于 1 时，JSON 与摘要中的 `min` / `max` / `mean` 对应该多次运行的统计量。
