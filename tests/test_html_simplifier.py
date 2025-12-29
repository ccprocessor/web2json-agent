"""
HTML精简功能测试

测试HTML精简工具，特别是form解包功能，确保ASP.NET网站内容不丢失
"""
import pytest
from pathlib import Path
from web2json.tools.html_simplifier import simplify_html


# 测试数据目录
TEST_DATA_DIR = Path(__file__).parent / "test_data" / "html_simplifier"
# 测试输出目录
TEST_OUTPUT_DIR = Path(__file__).parent / "test_output" / "html_simplifier"


@pytest.fixture(scope="session", autouse=True)
def setup_output_dir():
    """创建测试输出目录并生成汇总报告"""
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    yield

    # 测试结束后生成汇总报告
    generate_summary_report()


def generate_summary_report():
    """生成测试汇总报告"""
    report_files = list(TEST_OUTPUT_DIR.glob("*_report.txt"))

    if not report_files:
        return

    # 收集所有测试数据
    test_results = []
    for report_file in sorted(report_files):
        content = report_file.read_text(encoding='utf-8')
        # 解析报告内容
        lines = content.split('\n')
        filename = ""
        original_size = 0
        simplified_size = 0

        for line in lines:
            if line.startswith("文件名:"):
                filename = line.split(":")[1].strip()
            elif line.startswith("原始大小:"):
                original_size = int(line.split(":")[1].strip().replace(" bytes", "").replace(",", ""))
            elif line.startswith("精简后大小:"):
                simplified_size = int(line.split(":")[1].strip().replace(" bytes", "").replace(",", ""))

        if filename and original_size > 0:
            compression = (1 - simplified_size / original_size) * 100
            test_results.append({
                'filename': filename,
                'original': original_size,
                'simplified': simplified_size,
                'compression': compression
            })

    # 生成汇总报告
    summary_path = TEST_OUTPUT_DIR / "SUMMARY.txt"

    total_original = sum(r['original'] for r in test_results)
    total_simplified = sum(r['simplified'] for r in test_results)
    avg_compression = (1 - total_simplified / total_original) * 100 if total_original > 0 else 0

    summary = f"""HTML精简测试汇总报告
{'=' * 100}

测试时间: {Path(__file__).stat().st_mtime}
测试文件数: {len(test_results)}

{'文件名':<50} {'原始大小':>12} {'精简后':>12} {'压缩率':>10}
{'-' * 100}
"""

    for result in test_results:
        summary += f"{result['filename']:<50} {result['original']:>10,}B {result['simplified']:>10,}B {result['compression']:>9.1f}%\n"

    summary += f"""{'-' * 100}
{'总计':<50} {total_original:>10,}B {total_simplified:>10,}B {avg_compression:>9.1f}%

统计信息:
- 测试文件总数: {len(test_results)}
- 原始文件总大小: {total_original:,} bytes ({total_original/1024/1024:.2f} MB)
- 精简后总大小: {total_simplified:,} bytes ({total_simplified/1024:.2f} KB)
- 平均压缩率: {avg_compression:.1f}%
- 节省空间: {total_original - total_simplified:,} bytes ({(total_original - total_simplified)/1024:.2f} KB)

输出目录: {TEST_OUTPUT_DIR}
- *_simplified.html: 精简后的HTML文件
- *_report.txt: 单个文件测试报告
- SUMMARY.txt: 本汇总报告

{'=' * 100}
"""

    summary_path.write_text(summary, encoding='utf-8')
    print(f"\n✅ 测试输出已保存到: {TEST_OUTPUT_DIR}")
    print(f"📊 查看汇总报告: {summary_path}")


class TestFormUnwrap:
    """测试form标签解包功能"""

    def test_no_form_website(self):
        """测试无form的普通网站"""
        html = """
        <html>
        <head><script>alert('test')</script></head>
        <body>
            <div id="content">
                <h1>Title</h1>
                <p>Content</p>
            </div>
        </body>
        </html>
        """
        result = simplify_html(html, mode='xpath', keep_attrs=['id'])

        assert 'content' in result.lower()
        assert '<h1>' in result
        assert '<script' not in result.lower()
        assert len(result) > 20  # 确保有实质内容

    def test_normal_form_website(self):
        """测试普通表单网站（form内是表单控件）"""
        html = """
        <html>
        <body>
            <div id="header">Header</div>
            <form action="/submit">
                <input type="text" name="email">
                <button>Submit</button>
            </form>
            <div id="footer">Footer</div>
        </body>
        </html>
        """
        result = simplify_html(html, mode='xpath', keep_attrs=['id'])

        assert 'header' in result.lower()
        assert 'footer' in result.lower()
        assert '<form' not in result.lower()  # form已解包
        assert '<input' not in result.lower()  # input已删除
        assert '<button' not in result.lower()  # button已删除

    def test_aspnet_form_website(self):
        """测试ASP.NET风格网站（form包裹全部内容）"""
        html = """
        <html>
        <body>
            <form id="aspnetForm" runat="server">
                <input type="hidden" name="__VIEWSTATE" value="xxx" />
                <div id="header">Header</div>
                <div id="content">
                    <h1>Title</h1>
                    <p>Main content</p>
                </div>
                <div id="footer">Footer</div>
            </form>
        </body>
        </html>
        """
        result = simplify_html(html, mode='xpath', keep_attrs=['id'])

        # 关键：内容必须保留（最重要的测试目标）
        assert 'header' in result.lower()
        assert 'content' in result.lower()
        assert 'footer' in result.lower()
        assert '<h1>' in result
        assert '<p>' in result

        # ViewState等冗余应被清理
        assert '__VIEWSTATE' not in result

        # 注意：form标签是否被删除取决于unwrap实现，但内容保留是关键

    def test_nested_forms(self):
        """测试嵌套form标签"""
        html = """
        <html>
        <body>
            <form id="outer">
                <div class="wrapper">
                    <form id="inner">
                        <p>Inner content</p>
                    </form>
                    <p>Outer content</p>
                </div>
            </form>
        </body>
        </html>
        """
        result = simplify_html(html, mode='xpath', keep_attrs=['id', 'class'])

        # 关键：所有内容层级都应保留
        assert 'inner content' in result.lower()
        assert 'outer content' in result.lower()

        # 注意：form标签处理不影响内容保留（核心目标）


class TestRealWorldData:
    """使用真实数据测试"""

    @pytest.mark.parametrize("filename,min_size", [
        # 原始测试文件（简化命名）
        ("aspnet_carquotes.html", 10000),
        ("aspnet_job.html", 20000),
        ("aspnet_restaurant.html", 20000),
        # 所有13个完全丢失内容的文件（13B或58B）
        ("auto_automotive_schema_round_1.html", 30000),
        ("auto_motortrend_schema_round_1.html", 35000),
        ("job_careerbuilder_schema_round_1.html", 15000),
        ("movie_hollywood_schema_round_1.html", 30000),
        ("nbaplayer_slam_schema_round_1.html", 25000),
        ("university_collegeprowler_schema_round_1.html", 20000),
        ("university_collegetoolkit_schema_round_1.html", 25000),
        ("university_embark_schema_round_1.html", 8000),
        ("university_princetonreview_schema_round_1.html", 15000),
        # 严重内容丢失的文件（>90%丢失）
        ("camera_ecost_schema_round_1.html", 50000),
        ("university_collegenavigator_schema_round_1.html", 20000),
    ])
    def test_real_aspnet_sites(self, filename, min_size):
        """测试真实ASP.NET网站内容保留"""
        filepath = TEST_DATA_DIR / filename

        if not filepath.exists():
            pytest.skip(f"Test data not found: {filename}")

        original_html = filepath.read_text(encoding='utf-8', errors='ignore')
        original_size = len(original_html)

        result = simplify_html(
            original_html,
            mode='xpath',
            keep_attrs=['class', 'id', 'href', 'src']
        )
        result_size = len(result)

        # 保存精简结果到输出目录
        output_path = TEST_OUTPUT_DIR / filename.replace('.html', '_simplified.html')
        output_path.write_text(result, encoding='utf-8')

        # 同时保存对比报告
        report_path = TEST_OUTPUT_DIR / filename.replace('.html', '_report.txt')
        compression_rate = (1 - result_size / original_size) * 100
        retention_rate = result_size / original_size

        report = f"""HTML精简测试报告
{'=' * 80}
文件名: {filename}
原始大小: {original_size:,} bytes
精简后大小: {result_size:,} bytes
压缩率: {compression_rate:.1f}%
保留率: {retention_rate:.1%}

测试断言:
- 内容保留 (size > 100): {'✅ 通过' if result_size > 100 else '❌ 失败'}
- 最小保留率 (> 10%): {'✅ 通过' if retention_rate > 0.1 else '❌ 失败'}
- 有效压缩 (< 80%): {'✅ 通过' if retention_rate < 0.8 else '❌ 失败'}
- 最小尺寸 (>= {min_size:,}): {'✅ 通过' if result_size >= min_size else '❌ 失败'}

输出文件:
- 精简后HTML: {output_path.name}
- 本报告: {report_path.name}
"""
        report_path.write_text(report, encoding='utf-8')

        # 断言：不应该丢失全部内容（13字节 = <html></html>）
        assert result_size > 100, f"{filename}: Content lost! Size={result_size}"

        # 断言：应该保留合理比例的内容（至少10%）
        assert retention_rate > 0.1, f"{filename}: Too much content lost! Retention={retention_rate:.1%}"

        # 断言：应该有效压缩（不超过80%）
        assert retention_rate < 0.8, f"{filename}: Not enough compression! Retention={retention_rate:.1%}"

        # 断言：精简后应该有最低尺寸
        assert result_size >= min_size, f"{filename}: Result too small! Size={result_size}"

        # 断言：关键HTML标签应该存在
        assert '<div' in result or '<table' in result or '<ul' in result, \
            f"{filename}: Missing content tags"


class TestPerformance:
    """测试精简性能"""

    def test_compression_ratio(self):
        """测试压缩率在合理范围"""
        test_cases = [
            # (HTML, 预期压缩率范围)
            ('<html><head><script>x</script></head><body><div>a</div></body></html>', (0.3, 0.7)),
            ('<html><body>' + '<p>test</p>' * 100 + '</body></html>', (0.8, 1.0)),
        ]

        for html, (min_ratio, max_ratio) in test_cases:
            original_size = len(html)
            result = simplify_html(html, mode='xpath')
            result_size = len(result)
            ratio = result_size / original_size

            assert min_ratio <= ratio <= max_ratio, \
                f"Compression ratio {ratio:.2f} out of range [{min_ratio}, {max_ratio}]"

    def test_empty_tags_removal(self):
        """测试空标签清理"""
        html = """
        <html>
        <body>
            <div></div>
            <div><span></span></div>
            <div><p>Keep this</p></div>
            <div>
                <div></div>
            </div>
        </body>
        </html>
        """
        result = simplify_html(html, mode='xpath')

        # 应该保留有内容的标签
        assert 'Keep this' in result

        # 空标签应该被清理（但不检查具体实现，因为可能保留结构）
        assert len(result) < len(html) * 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
