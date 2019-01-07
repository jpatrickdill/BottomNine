const fs = require("fs");
const Scratch = require("scratch-api");

const PROJECT_ID = 277359774;

let config = JSON.parse(fs.readFileSync("./../config.json"));

let SCRATCH_USER = config.SCRATCH_USER;
let SCRATCH_PASS = config.SCRATCH_PASS;

const CHARS = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890~`!@#$%^&*()_-+={[}]|\\:;\"'<,>.?/";

function decode(encoded) {
    // Decodes string of numbers to normal string

    let str = "";

    for (let i = 0; i < encoded.length; i += 2) {
        let code = parseInt(encoded.slice(i, i + 2)) - 1;

        str += CHARS[code];
    }

    return str;
}

function encode(str) {
    // Encode string for cloud var

    let encoded = "";

    for (let i = 0; i < str.length; i++) {
        let code = CHARS.indexOf(str[i]);

        if (code === -1) {
            code = 0;
        }

        code = (code + 1).toString();
        code = "0" * (code.length - 2) + code; // pad with 0s

        encoded += code;
    }

    return encoded
}

function set(name, value) {
    // scratch cloud server (kinda)

    Scratch.UserSession.create(SCRATCH_USER, SCRATCH_PASS, (err, user) => {
        console.log("logged in");

        user.cloudSession(PROJECT_ID, (err, session) => {
            console.log("connected to cloud");

            session.set(name, value)
        })
    });
}

set();