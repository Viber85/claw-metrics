import {Component,type ReactNode} from 'react';
import {DialogButton,Focusable,Navigation} from '@decky/ui';
import {traceEditor} from '../modular/editor-page';

export class UiBoundary extends Component<{children:ReactNode;onExit?:()=>void},{failed:boolean}>{
 state={failed:false};
 static getDerivedStateFromError(){return {failed:true}}
 componentDidCatch(error:Error){console.error('Claw Metrics UI error',error);traceEditor('ui_error',String(error))}
 render(){
  if(!this.state.failed)return this.props.children;
  const close=this.props.onExit||(()=>Navigation.CloseSideMenus());
  return <Focusable flow-children="column" onCancelButton={event=>{event.preventDefault();event.stopPropagation();close()}} style={{padding:20,color:'#ffffff',background:'#121922'}}>
   <div role="alert">Claw Metrics could not display this page. The error was recorded.</div>
   <DialogButton onClick={close}>Close</DialogButton>
  </Focusable>;
 }
}
