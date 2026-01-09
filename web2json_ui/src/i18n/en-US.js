export default {
  header: {
    title: 'Web2JSON',
    subtitle: 'AI-Powered XPath Generator'
  },
  step1: {
    title: '📄 Step 1: Input HTML Samples',
    hint: '💡 Tip: Provide 2-5 similar pages for better XPath accuracy',
    uploadFiles: '📁 Upload Files',
    htmlSource: '📝 HTML Source',
    selectFiles: 'Select Files',
    selectFolder: 'Select Folder',
    clickToSelect: 'Click to select files',
    clickToSelectFolder: 'Click to select folder',
    noFileSelected: 'No file selected',
    filesSelected: '{count} file(s) selected',
    sampleLabel: 'Sample',
    addHtmlSample: '+ Add HTML Sample',
    pasteHtmlPlaceholder: 'Paste HTML content here...',
    samplesCount: 'Samples:',
    iterationEnabled: '(Iteration mode enabled ✨)'
  },
  step2: {
    title: '🏷️ Step 2: Define Fields',
    fieldName: 'Field name *',
    fieldDescription: 'Description (optional, but recommended)',
    addField: '+ Add Field',
    types: {
      string: 'String',
      int: 'Int',
      float: 'Float',
      bool: 'Bool',
      array: 'Array'
    }
  },
  step3: {
    generateButton: '✨ Generate XPath',
    generating: '🔄 Generating XPath...',
    processing: 'Processing {count} sample(s), please wait...'
  },
  step4: {
    title: '✅ Generated XPaths',
    noXpath: '(No XPath generated)',
    copyTooltip: 'Copy XPath',
    sampleValues: 'Sample Values:',
    moreValues: '... and {count} more'
  },
  messages: {
    copied: '✅ XPath copied to clipboard!',
    copyFailed: '❌ Failed to copy',
    fieldRequired: 'Please add at least one field'
  },
  common: {
    remove: 'Remove'
  },
  tabs: {
    xpathGeneration: 'XPath Generation',
    parserGeneration: 'Full Parser Generation'
  },
  parserTab: {
    step1: 'Step 1: Input HTML Samples',
    hint: 'Provide HTML samples and AI will automatically analyze and generate complete parser code',
    step2: 'Step 2: Select Schema Mode',
    step3: 'Step 3: Select Output Type',
    autoMode: 'Auto Mode',
    autoHint: 'AI automatically analyzes HTML and discovers all fields',
    predefinedMode: 'Predefined Mode',
    predefinedHint: 'You specify the field names to extract',
    structuredDataMode: 'Generate Structured Data',
    structuredDataHint: 'Generate complete parser code and output JSON formatted structured data',
    xpathMode: 'Generate XPath',
    xpathHint: 'Generate XPath expressions for fields only',
    generate: 'Generate Parser',
    startGenerate: 'Start extracting',
    generating: 'Generating...',
    progressTitle: 'Generation Progress',
    currentPhase: 'Current Phase',
    phases: {
      planning: 'Planning',
      schema_iteration: 'Extracting and Merging Schema',
      code_generation: 'Generating Parser Code',
      batch_parsing: 'Batch Parsing HTML Files',
      packaging: 'Packaging Results'
    },
    cancel: 'Cancel Task',
    cancelling: 'Cancelling...',
    resultsTitle: 'Generation Results',
    downloadJsonl: 'Download JSONL',
    downloadCsv: 'Download CSV',
    downloadZip: 'Download ZIP (Full Package)',
    downloadParser: 'Download parser.py',
    previewTitle: 'Results Preview',
    showing10Rows: 'Showing first 10 rows of {total} total',
    moreRows: '... and {count} more rows (download file to view all)',
    moreResults: '... and {count} more files (download ZIP to view all)'
  },
  configModal: {
    title: 'API Configuration',
    apiKeyPlaceholder: 'Enter your API Key',
    apiKeyHint: 'OpenAI or compatible API key',
    apiBasePlaceholder: 'https://api.openai.com/v1',
    apiBaseHint: 'Base URL for the API service',
    iterationRounds: 'Iteration Learning Samples',
    iterationRoundsPlaceholder: '3',
    iterationRoundsHint: 'Number of HTML samples for learning (default: 3)',
    save: 'Save',
    saving: 'Saving...',
    cancel: 'Cancel',
    saveSuccess: 'Saved successfully!',
    saveFailed: 'Failed to save',
    noChanges: 'No changes made',
    copy: 'Copy',
    copied: 'Copied!',
    copyFailed: 'Failed to copy'
  }
}
