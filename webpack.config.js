var path = require('path');

module.exports = {
    context: path.resolve(__dirname, 'paguen_po', 'static_src'),
    entry: {
        'core/index': './core/index.js'
    },
    output: {
        path: path.resolve(__dirname, 'paguen_po', 'static', 'dist'),
        filename: "[name].js",
        publicPath: "./dist"
    },
    resolve: {
        extensions: ['.js', '.vue'],
        alias: {
            'vue$': 'vue/dist/vue.esm.js',
            'static_src': path.resolve(__dirname, 'paguen_po', 'static_src')
        }
    },
    module: {
        rules: [
            {
                test: /\.css$/,
                loaders: 'style-loader!css-loader'
            },
            {
                test: /\.less$/,
                loader: "style-loader!css-loader!less-loader"
            },
            {
                test: /\.js$/,
                exclude: /node_modules/,
                loader: "babel-loader"
            },
            {
                test: /\.vue$/,
                loader: 'vue-loader'
            },
            {
                test: /\.(jpe|jpg|woff|woff2|eot|ttf|svg)(\?.*$|$)/,
                loader: 'url-loader?limit=50000&name=fonts/[name].[ext]'
            },
            {
                test: /\.(png)(\?.*$|$)/,
                loader: 'url-loader?limit=50000&name=img/[name].[ext]'
            }
        ]
    }
};