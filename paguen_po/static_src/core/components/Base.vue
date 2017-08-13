<template>
    <div>
        <input type="text" v-model="asdf">
        <p v-text="asdf"></p>
    </div>
</template>

<script>
    export default {
        name: "paguenpo",
        data () {
            return {
                asdf: "holaaa"
            };
        }
    }
</script>