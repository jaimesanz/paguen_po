let path = require('path');

module.exports = {
    context: path.resolve(__dirname, 'paguen_po', 'static_src'),
    entry: {
        'core/index': './core/index.js'
    },
    output: {
        path: path.resolve(__dirname, 'paguen_po', 'static', 'dist'),
        filename: "[name].js",
        publicPath: "./static/dist/"
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
                test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
                use: [
                    {
                        loader: 'url-loader',
                        options: {
                            limit: 10000,
                            mimetype: 'application/font-woff'
                        }
                    }
                ]
            },
            {
                test: /\.(ttf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
                use: [
                    { loader: 'file-loader' }
                ]
            }
        ]
    }
};