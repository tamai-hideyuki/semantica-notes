module.exports = {
    rewrites: async () => [
        {
            source: '/api/:path*',
            destination: 'http://localhost:8000/api/:path*',
        },
    ]
}
