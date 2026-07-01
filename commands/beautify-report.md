# /beautify-report - 报告美化

将 Markdown 格式的初次覆盖报告转换为高可读性的 HTML 文件。

## 用法

```text
/beautify-report 002463-沪电股份
```

## 执行流程

1. 调用 `analyst-beautifier`。
2. 确认目标标的目录存在：
   `reports/stocks/{代码}-{名称}/01-初次覆盖/`
3. 检查首席报告和四份子报告是否存在。
4. 运行：

```bash
python tools/md-to-html.py <代码-名称>
```

5. 返回 HTML 文件输出路径。

## 输出

HTML 文件会生成在目标标的的初次覆盖目录下，用于浏览器阅读和分享。
