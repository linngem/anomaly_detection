new Vue({
    el: '#app',
    data: {
        file: null,
        columns: [],
        selectedColumns: [],
        contamination: 0.05,
        result: null
    },
    methods: {
        // Handle file upload and get columns
        uploadFile() {
            if (!this.$refs.file.files[0]) {
                alert('Please select a file to upload.');
                return;
            }

            let formData = new FormData();
            formData.append('file', this.$refs.file.files[0]);

            axios.post('http://127.0.0.1:5000/get_columns', formData)
                .then(response => {
                    this.columns = response.data.columns;
                })
                .catch(error => {
                    alert('Error uploading file: ' + error.response?.data?.error || error.message);
                });
        },

        // Handle anomaly detection
        detectAnomalies() {
            if (!this.file) {
                alert('Please upload a file.');
                return;
            }

            if (this.selectedColumns.length === 0) {
                alert('Please select at least one column for anomaly detection.');
                return;
            }

            let formData = new FormData();
            formData.append('file', this.$refs.file.files[0]);
            formData.append('columns', JSON.stringify(this.selectedColumns));
            formData.append('contamination', this.contamination);

            axios.post('http://127.0.0.1:5000/upload', formData)
                .then(response => {
                    this.result = response.data;  // Assign result data here
                    console.log(this.result); // Log to inspect result structure
                })
                .catch(error => {
                    alert('Error detecting anomalies: ' + error.response?.data?.error || error.message);
                });
        }
    }
});

