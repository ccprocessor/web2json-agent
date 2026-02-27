from web2json import Web2JsonConfig, classify_html_dir, extract_data
import os

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

    # Get cluster directory path
    cluster_dir = os.path.join(
        classify_config.output_path or "output",
        classify_config.name,
        "clusters",
        cluster_name
    )

    # Create extraction config for this cluster
    extract_config = Web2JsonConfig(
        name=f"{classify_config.name}_{cluster_name}",
        html_path=cluster_dir,
        save=['schema', 'code', 'data'],  # Save schema, code, and extracted data
        iteration_rounds=min(3, len(files)),  # Use min(3, file_count) samples for learning
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