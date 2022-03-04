document.querySelectorAll("button").forEach(btn => {
    btn.addEventListener("click", e => {
        e.preventDefault()
        e.stopPropagation()
        btn.classList.add("is-loading")
        toggleSelectedButton(btn)
        const ad = e.target.innerText
        fetch(`/metar/${ad}`)
            .then(r => r.json())
            .catch(err => console.error(err))
            .then(r => {
                document.getElementById("metar_data").innerHTML = r.metar
                btn.classList.remove("is-loading")
            })
            .catch(err => console.error(err))
    })
})

function toggleSelectedButton(btn) {
    document.querySelectorAll("button").forEach(button => {
        if (button !== btn) {
            button.classList.remove("is-selected", "is-info")
        } else {
            button.classList.add("is-selected", "is-info")
        }
    })
}