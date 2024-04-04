document.addEventListener('DOMContentLoaded', function() {
    let dropArea = document.getElementById('drop-area');

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() { dropArea.classList.add('highlight'); }
    function unhighlight() { dropArea.classList.remove('highlight'); }

    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        let dt = e.dataTransfer;
        let files = dt.files;

        handleFiles(files);
    }

    function handleFiles(files) {
        ([...files]).forEach(uploadFile);
    }

    function uploadFile(file) {
        // Implement the upload logic here
        console.log(file);
    }

    // Listen for the save button click to initiate the upload process
    document.getElementById('saveBtn').addEventListener('click', function() {
        let inputFiles = document.getElementById('fileElem').files;
        handleFiles(inputFiles);
    });
});
