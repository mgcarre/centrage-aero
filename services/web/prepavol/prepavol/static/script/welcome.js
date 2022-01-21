const urls = ["/metar/", null]
document.querySelectorAll("button").forEach(btn => {
    btn.addEventListener("click", e => {
        e.preventDefault()
        e.stopPropagation()
        const ad = e.target.innerText
        Promise.all([requestApi(urls[0], ad, "taf"), requestApi(urls[1], ad, "metar")]).catch(err => console.error(err))
    })
})
function requestApi(url, ad, type) {
    if (url == null) return
    return fetch(`${url}${ad}`)
        .then(r => r.json()).catch(err => console.error(err))
        .then(r => {
            if (r.length == 0) {
                throw new Error("Aucune réponse du serveur")
            }
            alert(r.metar)
        })
        .catch(err => console.error(err))
}