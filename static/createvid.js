let selectedImages = [];

document.addEventListener('DOMContentLoaded', function() {
    fetchImages();
    fetchAvailableAudios();
});

function fetchImages() {
    fetch('/user_images', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    })

    .then(response => response.json())
    .then(data => {
        const imagesContainer = document.getElementById('uploaded-images');
        imagesContainer.innerHTML = ''; // Clear existing
        data.images.forEach(imageData => {
            let imgDiv = document.createElement('div');
            let img = document.createElement('img');
            img.src = `data:image/${imageData.format};base64,${imageData.image}`;
            img.alt = 'Uploaded Image';
            img.style.width = '100px'; // Example size, adjust as needed
            img.style.height = '100px';

            let addButton = document.createElement('button');
            addButton.textContent = 'Add to List';
            addButton.addEventListener('click', function() { addToList(img); addToList2(imageData.id, img.src); }); 
            imgDiv.appendChild(img);
            imgDiv.appendChild(addButton);
            imagesContainer.appendChild(imgDiv);
        });
    })
    .catch(error => console.error('Error fetching images:', error));
}
function addToList2(filename, src) {
    if (!selectedImages.includes(filename)) { // Prevent duplicate entries
        selectedImages.push(filename);
        updateSelectedImagesList(src);
    }
}

function updateSelectedImagesList(src) {
    const list = document.getElementById('selected-images');
    // Instead of clearing and repopulating the list, just add the new image
    let img = document.createElement('img');
    img.src = src;
    img.alt = 'Selected Image';
    img.style.width = '100px'; // Match the size with uploaded images or as needed
    img.style.height = '100px';
    img.style.margin = '5px'; // Add some space around the images
    list.appendChild(img);
}
function addToList(imgElement) {
    // Extract image data URI from imgElement
    const imageDataURI = imgElement.src;
    
    // Send image data URI to server
    fetch('/save_image', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ image: imageDataURI }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error saving image on the server');
        }
        console.log('Image saved on the server');
    })
    .catch(error => console.error('Error saving image on the server:', error));
}
// function selectAudio(filename) {
//     selectedAudio = filename;
//     updateSelectedAudio();
// }

// function updateSelectedAudio() {
//     const selectedAudioContainer = document.getElementById('selected-audio');
//     selectedAudioContainer.innerHTML = ''; // Clear existing
//     if (selectedAudio) {
//         let audioName = document.createElement('p');
//         audioName.textContent = Selected Audio:${selectedAudio};
//         selectedAudioContainer.appendChild(audioName);
//     }
// }
// Event listener for create video button
let selectedAudio = null;

function selectAudio(audioUrl) {
    const audioFileName = audioUrl.split('/').pop();
   
    selectedAudio = audioUrl;
    updateSelectedAudio();
}

function updateSelectedAudio() {
    const selectedAudioContainer = document.getElementById('selected-audio');
    selectedAudioContainer.innerHTML = ''; // Clear existing
    if (selectedAudio) {
        let audioName = document.createElement('p');
        audioName.textContent = `Selected Audio: ${selectedAudio}`;
        selectedAudioContainer.appendChild(audioName);
    }
}
// Function to fetch available audio files from the server
function fetchAvailableAudios() {
    fetch('/available_audios', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        const audioList = document.getElementById('audio-list');
        audioList.innerHTML = ''; // Clear existing list
        data.forEach(audio => {
            const button = document.createElement('button');
            button.textContent = audio.name;
            button.addEventListener('click', function() {
                selectAudio(audio.url);
            });
            audioList.appendChild(button);
        });
    })
    .catch(error => console.error('Error fetching available audios:', error));
}

function selectAudio(audioSrc) {
    // Extract the filename from the URL
    let filename = audioSrc.split('/').pop();
    // Set the selected audio source
    let audioElement = document.getElementById("selected-audio");
    audioElement.textContent = `Selected Audio: ${filename}`;
    // Store the selected audio source (filename only) in the hidden input field
    document.getElementById("audio-src").value = filename;
}


