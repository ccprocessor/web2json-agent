from web2json import Web2JsonConfig, classify_html_dir, extract_data
import os
import shutil
from pathlib import Path

# Step 1: Classify HTML files by layout
classify_config = Web2JsonConfig(
    name="classify_demo",
    html_path="input_html/mixed_input/",
    # save=['report', 'files'],  # Save cluster report and copy files to subdirectories
    # output_path="./cluster_analysis",  # Custom output directory
)

classify_result = classify_html_dir(classify_config)

print(f"\n{'='*60}")
print(f"布局分类完成")
print(f"{'='*60}")
print(f"识别出的布局类型: {classify_result.cluster_count}")
print(f"噪声文件: {len(classify_result.noise_files)}")

for cluster_name, files in classify_result.clusters.items():
    print(f"\n{cluster_name}: {len(files)} 个文件")
    for file in files[:3]:
        print(f"  - {os.path.basename(file)}")

# Step 2: Extract data for each cluster
print(f"\n{'='*60}")
print(f"开始对每个布局类型进行数据提取")
print(f"{'='*60}")

extraction_results = {}

for cluster_name, files in classify_result.clusters.items():
    print(f"\n处理 {cluster_name} ({len(files)} 个文件)...")

    # Determine HTML path: use cluster directory if files were saved, otherwise create temp directory
    if classify_config.should_save_item('files'):
        # If files were saved, use the cluster directory
        html_path = os.path.join(
            classify_config.output_path or "output",
            classify_config.name,
            "clusters",
            cluster_name
        )
    else:
        # If files were not saved, create a temporary directory and copy files
        temp_cluster_dir = Path("output") / classify_config.name / "temp_clusters" / cluster_name
        temp_cluster_dir.mkdir(parents=True, exist_ok=True)

        # Copy cluster files to temp directory
        for src_file in files:
            src = Path(src_file)
            dst = temp_cluster_dir / src.name
            shutil.copy2(src, dst)

        html_path = str(temp_cluster_dir)

    # Create extraction config for this cluster
    extract_config = Web2JsonConfig(
        name=f"{classify_config.name}_{cluster_name}",
        html_path=html_path,
        save=['schema', 'code', 'data'],  # Save schema, code, and extracted data
        # schema={
        #     "title": "string",
        #     "date": "string",
        # },
        output_path="./testoutput",  # Custom output directory
    )

    # Extract data
    try:
        result = extract_data(extract_config)
        extraction_results[cluster_name] = result
        print(f"✓ {cluster_name} 数据提取完成")
        print(f"  生成的 schema 字段数: {len(result.final_schema) if result.final_schema else 0}")
        print(f"  解析的文件数: {len(result.parsed_data)}")
    except Exception as e:
        print(f"✗ {cluster_name} 数据提取失败: {e}")
        extraction_results[cluster_name] = None

# Clean up temp directories if they were created
if not classify_config.should_save_item('files'):
    temp_clusters_dir = Path("output") / classify_config.name / "temp_clusters"
    if temp_clusters_dir.exists():
        shutil.rmtree(temp_clusters_dir)
        print(f"\n✓ 已清理临时目录: {temp_clusters_dir}")

# Step 3: Summary
print(f"\n{'='*60}")
print(f"全部完成")
print(f"{'='*60}")
print(f"总布局类型: {classify_result.cluster_count}")
print(f"成功提取数据的类型: {sum(1 for r in extraction_results.values() if r is not None)}")

for cluster_name, result in extraction_results.items():
    if result:
        output_dir = os.path.join("output", f"{classify_config.name}_{cluster_name}")
        print(f"\n{cluster_name}:")
        print(f"  结果目录: {output_dir}")
        print(f"  解析文件数: {len(result.parsed_data)}")
        print(f"  Schema 字段: {list(result.final_schema.keys()) if result.final_schema else []}")