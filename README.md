# drive-kesma-library-linker

LINE bot to deliver links of e-books from HIMASTA-ITS Kesma Library straight through chat. Also, a helper to do my attendance (absensi) for me. Inherently a for-myself project.

# Keywords

The bot will not respond to chats unless they include these keywords:

## `*auth`

Usage: `*auth USERNAME PASSWORD`

What it does: Saves/updates your authorization detail. The bot has to save your authorization detail before you can use it to do absensi. The authorization detail is associated with your LINE account. Please don't use this on device that is not your own because doing so has large consequences.

## `*deauth`

Usage: `*deauth`

What it does: Removes/forgets the authorization detail previously associated with your LINE account.

## `!` (key absen identifier)

Usage: `!MATKUL KODE_PRESENSI`

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
