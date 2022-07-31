#include <stdio.h>
#include "ed25519.h"

int main() {
    //binding to py
    /***
     * get 32 bytes private key from python, as well as a message in bytes along with its length
     */

    //works if we just treat seed as the private key
    unsigned char seed[] = {28, 120, 204, 1, 190, 161, 83, 82, 182, 60, 86, 151, 241, 207, 225, 47, 253, 209, 109, 220,
                            29, 89, 231, 121, 81, 182, 233, 64, 142, 226, 40, 173};
    unsigned char private[32];
    unsigned char public[32];
    unsigned char signature[64];
    unsigned char msgchars[] = {84, 69, 83, 84, 32, 77, 69, 83, 83, 65, 71, 69};


    ed25519_create_keypair(public, private, seed);
    ed25519_sign2(signature, msgchars, 12, public, private,seed);
//    ed25519_sign(signature, msgchars, 12, public, private);
    int v = ed25519_verify(signature, msgchars, 12, public);


    printf("pub: [");
    for (int i = 0; i < 31; ++i) {
        printf("%d, ", public[i]);
    }
    printf("%d]\n", public[31]);

    printf("sig:   [");
    for (int i = 0; i < 63; ++i) {
        printf("%d, ", signature[i]);
    }
    printf("%d]\n", signature[63]);


    printf("verification: %s", v ? "True" : "False");
    return 0;
}