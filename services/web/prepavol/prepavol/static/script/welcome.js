document.querySelectorAll("button").forEach(btn => {
    btn.addEventListener("click", e => {
        e.preventDefault()
        e.stopPropagation()
        const ad = e.target.innerText
        fetch(`/metar/${ad}`)
            .then(r => r.json())
            .catch(err => console.error(err))
            .then(r => alert(r.metar))
            .catch(err => console.error(err))
    })
})