function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function handleResponse(response) {
  if (response.status === 204) {
    return '';
  } else if (response.status === 404) {
    return null
  } else {
    return response.json();
  }
}

function apiService(endpoint, method, data) {
  const config = {
    method: method || "GET",
    body: data !== undefined ? JSON.stringify(data) : null,
    headers: {
      'content-type': 'application/json',
      'X-CSRFTOKEN': getCookie('csrftoken')
    }
  };
  return fetch(endpoint, config)
      .then(handleResponse)
      .catch(error => console.log(error))
}

function filesApiService(endpoint, files) {
      let formData = new FormData()
      for( let file of files ) {
          formData.append(file.name, file);
      }

      return fetch(endpoint, {
          method: 'POST',
          headers: {
              "X-CSRFToken": getCookie('csrftoken')
          },
          body: formData
      }).then(handleResponse).catch(error => { console.log(error)});
}

function fileApiService(endpoint, method, fieldName, file) {
  let data = new FormData(); // creates a new FormData object
  data.append(fieldName, file); // add your file to form data

  const config = {
    method: method,
    body: data,
    headers: {
      'X-CSRFTOKEN': getCookie('csrftoken')
    }
  };
  return fetch(endpoint, config)
      .then(handleResponse)
      .catch(error => console.log(error))
}

function groomJSON(json) {
  return JSON.stringify(json).replaceAll("{", "").replaceAll("}", "").replaceAll("[", " ").replaceAll("]", " ").replaceAll('"', "").replaceAll("non_field_errors:", "")
}

