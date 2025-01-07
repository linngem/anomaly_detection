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
            console.log('Uploading file...');
            let formData = new FormData();
            formData.append('file', this.$refs.file.files[0]);

            axios.post('/get_columns', formData)
                .then(response => {
                    console.log('Columns received:', response.data.columns);
                    this.columns = response.data.columns;
                    console.log(this.columns);  // Check if columns are received correctly
                })
                .catch(error => {
                    alert('Error uploading file: ' + (error.response?.data?.error || error.message));
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

            axios.post('/upload', formData)
                .then(response => {
                    console.log(response.data);  // Check the returned data
                    this.result = response.data;  // Store the result of the anomaly detection
                })
                .catch(error => {
                    console.error("Error uploading file:", error);
                });
        }
    }
});
