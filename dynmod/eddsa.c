#include "py/dynruntime.h"
//#include <string.h>
#include "ed25519.h"



//function that gets exposed to python
//this demonstrates how the C library interacts with python on the
//example of keygen, but we also test signature and verification
//error when trying to import the module
//Traceback (most recent call last):
//  File "<stdin>", line 1, in <module>
//MemoryError: memory allocation failed, allocating 37660 bytes

STATIC mp_obj_t keygen(mp_obj_t o){
    size_t key_len = 32;
    unsigned char private[key_len];
    unsigned char public[key_len];
    unsigned char signature[64];

    if(mp_obj_get_type(o) == &mp_type_bytes){

        unsigned char* seed;
        size_t len;
        seed = mp_obj_str_get_data(o, &len);


    // test msg
    //this throws a linker error telling me memcpy is not found
//    unsigned char msgchars[] = {84, 69, 83, 84, 32, 77, 69, 83, 83, 65, 71, 69};
    unsigned char msgchars[12];
    msgchars[0]=84;
    msgchars[1]=69;
    msgchars[2]=83;
    msgchars[3]=84;
    msgchars[4]=32;
    msgchars[5]=77;
    msgchars[6]=83;
    msgchars[7]=83;
    msgchars[8]=85;
    msgchars[9]=71;
    msgchars[10]=71;
    msgchars[11]=69;



        ed25519_create_keypair(public, private, seed);
        ed25519_sign2(signature, msgchars, 12, public, private,seed);
        ed25519_verify(signature, msgchars, 12, public);


    return mp_obj_new_bytes(public, 32);

    }else{
    //not bytes
    return mp_const_false;
    }
}
//turn our function into a function object so the interpreter can work with it
STATIC MP_DEFINE_CONST_FUN_OBJ_1(keygen_obj, keygen);



//entrypoint, called when module is imported
mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
    //must be first, sets up global dict and other things
    MP_DYNRUNTIME_INIT_ENTRY


    //make function available in modules namespace
    mp_store_global(MP_QSTR_keygen, MP_OBJ_FROM_PTR(&keygen_obj));
    //must be last, restores global dict
    MP_DYNRUNTIME_INIT_EXIT
}
