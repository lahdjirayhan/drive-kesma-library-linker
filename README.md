# drive-kesma-library-linker

LINE bot to deliver links of e-books from HIMASTA-ITS Kesma Library straight through chat. Also, a helper to do my attendance (absensi) for me. Inherently a for-myself project.

# Keywords

The bot will not respond to chats unless they include these keywords:

## `*auth`

Usage: `*auth`

What it does: Sends you a link that displays a "Sign In" page. The page is not a sign-in system in any way, it is just there so that you can enter your authorization detail more securely [1]. After you press "Sign In" there, your authorization detail will be remembered and associated with your LINE account. You can then subsequently use the bot to do presensi.

Whatever password you enter in the "Sign In" page will not be checked whether it's correct. If doing presensi using `!` (see below) tells you that the login is unsuccessful, perhaps you have entered the wrong password/ In such case, you can use `*auth` to enter the "Sign In" page and update your password by entering the correct one.

Note: the login link can't be reused, but you can get another login link using `*auth` whenever you need.

## `*deauth`

Usage: `*deauth`

What it does: Removes/forgets the authorization detail previously associated with your LINE account.

## `!` (key absen identifier)

Usage: `!MATKUL KODE_PRESENSI`, e.g. `!ekon 123123`

What it does: Tells the bot to go filling your absensi:
1. Go to presensi(dot)its(dot)ac(dot)id
2. Login using authorization detail associated with your LINE account. If login fails/has wrong detail, terminate.
3. Infer the course that requires absensi:
    - Determine which course is the MATKUL keyword is pointing to. If appropriate course is found, select that course. Otherwise, declare MATKUL is not recognized and terminate.
    - Enter the selected course's page.
4. Infer the date that requires absensi:
    - Search for an entry that is marked with today's date, starting from latest schedule date to older schedule date. If found, select that entry. Otherwise,
    - Search for an entry that has its status not HADIR, starting from latest schedule date to older schedule date. If found, select that entry. Otherwise,
    - Declare that all entries in the course has been HADIR and terminate.
5. Enter the KODE_PRESENSI in the selected entry.
6. Return the status: successful, failed, or already HADIR; and terminate.

# Notes

 - [1] The "Sign In" login page is more secure compared to previous implementation of sending `*auth USERNAME PASSWORD` over LINE chat. That is because chats to official accounts can't be unsent. It can be deleted, but it has to be deleted individually on every device you are logged into (e.g. deleting it on your phone does not automatically deletes the chat history on your PC if you're logged in there, vice versa). It is a hassle and prone to be seen by people looking over your shoulder since in your display the password will be in cleartext (`PASSWORD` not `*******`).