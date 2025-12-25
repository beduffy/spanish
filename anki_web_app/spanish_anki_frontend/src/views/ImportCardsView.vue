<template>
  <div class="import-cards-view">
    <h1>Import Cards from CSV/TSV</h1>

    <div v-if="errorMessage" class="error-message">
      <p>{{ errorMessage }}</p>
    </div>

    <div v-if="successMessage" class="success-message">
      <p>{{ successMessage }}</p>
    </div>

    <div class="import-form">
      <form @submit.prevent="handleImport">
        <div class="form-group">
          <label for="file">CSV/TSV File *</label>
          <input type="file" id="file" @change="handleFileSelect" accept=".csv,.tsv" required />
          <small v-if="selectedFile">Selected: {{ selectedFile.name }}</small>
        </div>

        <div v-if="previewData" class="preview-section">
          <h3>File Preview</h3>
          <p>Available columns: {{ previewData.columns.join(', ') }}</p>
          <p>Total rows: {{ previewData.total_rows }}</p>

          <div class="form-group">
            <label for="frontColumn">Front Column *</label>
            <select id="frontColumn" v-model="frontColumn" required>
              <option value="">Select column...</option>
              <option v-for="col in previewData.columns" :key="col" :value="col">{{ col }}</option>
            </select>
          </div>

          <div class="form-group">
            <label for="backColumn">Back Column *</label>
            <select id="backColumn" v-model="backColumn" required>
              <option value="">Select column...</option>
              <option v-for="col in previewData.columns" :key="col" :value="col">{{ col }}</option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="language">Language (optional)</label>
              <input type="text" id="language" v-model="language" placeholder="e.g., es, de" />
            </div>

            <div class="form-group">
              <label>
                <input type="checkbox" v-model="createReverse" />
                Create reverse cards
              </label>
            </div>
          </div>

          <div v-if="previewData.preview && previewData.preview.length > 0" class="preview-table">
            <h4>Preview (first 5 rows):</h4>
            <table>
              <thead>
                <tr>
                  <th>Front</th>
                  <th>Back</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in previewData.preview" :key="idx">
                  <td>{{ row.front }}</td>
                  <td>{{ row.back }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="form-actions">
          <button v-if="selectedFile && !previewData" type="button" @click="previewFile" :disabled="isLoading" class="btn btn-secondary">
            {{ isLoading ? 'Loading...' : 'Preview File' }}
          </button>
          <button v-if="previewData" type="submit" :disabled="isImporting || !frontColumn || !backColumn" class="btn btn-primary">
            {{ isImporting ? 'Importing...' : 'Import Cards' }}
          </button>
          <router-link to="/cards" class="btn btn-secondary">Cancel</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import ApiService from '@/services/ApiService';

export default {
  name: 'ImportCardsView',
  data() {
    return {
      selectedFile: null,
      previewData: null,
      frontColumn: '',
      backColumn: '',
      language: '',
      createReverse: true,
      isLoading: false,
      isImporting: false,
      errorMessage: '',
      successMessage: ''
    };
  },
  methods: {
    handleFileSelect(event) {
      this.selectedFile = event.target.files[0];
      this.previewData = null;
      this.frontColumn = '';
      this.backColumn = '';
      this.errorMessage = '';
      this.successMessage = '';
    },
    async previewFile() {
      if (!this.selectedFile) return;

      this.isLoading = true;
      this.errorMessage = '';
      try {
        const response = await ApiService.importCards(
          this.selectedFile,
          '', // front_column - empty for preview
          '', // back_column - empty for preview
          this.language,
          this.createReverse,
          null, // delimiter - auto-detect
          true // preview_only
        );
        if (response.status === 200 && response.data) {
          this.previewData = response.data;
        }
      } catch (error) {
        console.error('Error previewing file:', error);
        this.errorMessage = error.response?.data?.error || 'Failed to preview file. Please check the file format.';
      } finally {
        this.isLoading = false;
      }
    },
    async handleImport() {
      if (!this.selectedFile || !this.frontColumn || !this.backColumn) {
        this.errorMessage = 'Please select a file and choose front/back columns.';
        return;
      }

      this.isImporting = true;
      this.errorMessage = '';
      this.successMessage = '';

      try {
        const response = await ApiService.importCards(
          this.selectedFile,
          this.frontColumn,
          this.backColumn,
          this.language,
          this.createReverse,
          null, // delimiter - auto-detect
          false // preview_only
        );

        if (response.status === 201 && response.data) {
          const { created_count, error_count, errors } = response.data;
          if (error_count > 0) {
            this.successMessage = `Imported ${created_count} cards successfully. ${error_count} errors occurred.`;
            if (errors && errors.length > 0) {
              console.warn('Import errors:', errors);
            }
          } else {
            this.successMessage = `Successfully imported ${created_count} cards!`;
          }
          // Reset form after successful import
          setTimeout(() => {
            this.$router.push('/cards');
          }, 2000);
        }
      } catch (error) {
        console.error('Error importing cards:', error);
        this.errorMessage = error.response?.data?.error || 'Failed to import cards. Please check the file format and try again.';
      } finally {
        this.isImporting = false;
      }
    }
  }
};
</script>

<style scoped>
.import-cards-view {
  padding: 20px;
  font-family: Arial, sans-serif;
  max-width: 900px;
  margin: 0 auto;
}

.error-message, .success-message {
  text-align: center;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.error-message {
  color: red;
  background-color: #ffe0e0;
}

.success-message {
  color: #155724;
  background-color: #d4edda;
}

.import-form {
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.form-group {
  margin-bottom: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #333;
}

input[type="file"],
input[type="text"],
select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1em;
  font-family: inherit;
}

small {
  display: block;
  margin-top: 5px;
  color: #666;
  font-size: 0.9em;
}

.preview-section {
  margin-top: 30px;
  padding-top: 30px;
  border-top: 2px solid #eee;
}

.preview-section h3 {
  margin-top: 0;
}

.preview-table {
  margin-top: 20px;
}

.preview-table h4 {
  margin-bottom: 10px;
}

.preview-table table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.preview-table th,
.preview-table td {
  padding: 8px 12px;
  border: 1px solid #ddd;
  text-align: left;
  font-size: 0.9em;
}

.preview-table thead {
  background-color: #f8f9fa;
}

.preview-table tbody tr:nth-child(even) {
  background-color: #f9f9f9;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.btn {
  padding: 10px 20px;
  border-radius: 4px;
  text-decoration: none;
  font-weight: bold;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s;
  display: inline-block;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-primary:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #545b62;
}

.btn-secondary:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style>
