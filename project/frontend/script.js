document.getElementById("loginButton").addEventListener("click", async () => {
  const apiUrl = document.getElementById("apiUrl").value;
  const loginUrl = `${apiUrl}/login`;
  const fileUrl = `${apiUrl}/files`;
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  fetch(loginUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
    mode: "cors",
  }).then((res) => res.text())
  .then(token => {
    ["tenant1", "tenant2"].forEach((tenant) => {
      const url = document.getElementById(`${tenant}Url`).textContent;
      fetch(`${fileUrl}/${url}`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        responseType: "arraybuffer",
        mode: "cors",
      })
        .then((response) => response.arrayBuffer())
        .then((arrayBuffer) => {
          const blob = new Blob([arrayBuffer]);
          const imageUrl = URL.createObjectURL(blob);
          const imgElement = document.getElementById(`${tenant}Img`);
          imgElement.src = imageUrl;
        });
    });
  })
  .catch((error) => {
    alert("Error: " + error);
  });
});
