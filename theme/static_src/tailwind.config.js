module.exports = {
    plugins: [
        require('@tailwindcss/typography'),
        require('daisyui')
    ],
    theme: {
        extend: {
            typography: {
                DEFAULT: {}
            }
        },
        daisyui: {
            themes: [ "silk", "black", ],
            darkTheme: "black",
            lightTheme: "silk",
            base: true,
            styled: true,
            utils: true
        }
    }
}
