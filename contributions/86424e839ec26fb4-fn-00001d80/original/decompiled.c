
int __cdecl FUN_00401d80(short *param_1)

{
  short sVar1;
  short *psVar2;

  psVar2 = param_1;
  do {
    sVar1 = *psVar2;
    psVar2 = psVar2 + 1;
  } while (sVar1 != 0);
  return ((int)psVar2 - (int)param_1 >> 1) + -1;
}
