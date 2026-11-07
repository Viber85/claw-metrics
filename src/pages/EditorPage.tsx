import {useEffect} from 'react';
import {DialogButton,Navigation} from '@decky/ui';
import {Builder} from '../modular/Builder';
import {UiBoundary} from '../components/UiBoundary';
import {currentEditorPage,leaveEditorPage,mountEditorPage} from '../modular/editor-page';

export function EditorPage(){
 const session=currentEditorPage();
 useEffect(()=>{
  if(!session)return;
  return mountEditorPage(session.id);
 },[session?.id]);
 if(!session)return <DialogButton onClick={()=>Navigation.NavigateBack()}>Back</DialogButton>;
 const close=()=>leaveEditorPage(session.id);
 return <UiBoundary onExit={close}><Builder {...session.props} closeModal={close}
  onApply={(layout,appearance,slot)=>leaveEditorPage(session.id,()=>session.props.onApply(layout,appearance,slot))}/></UiBoundary>;
}
