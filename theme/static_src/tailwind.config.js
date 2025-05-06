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
            themes: [ "light", "dark", "cupcake" ],
            darkTheme: "dark",
            base: true,
            styled: true,
            utils: true
        }
    }
}
